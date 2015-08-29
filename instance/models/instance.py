# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Instance app models - Instance
"""

# Imports #####################################################################

import logging
import os

from functools import partial

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.template import loader
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel

from instance import ansible, github
from instance.gandi import GandiAPI
from instance.github import fork_name2tuple, get_username_list_from_team
from instance.logging import log_exception
from instance.logger_adapter import InstanceLoggerAdapter
from instance.repo import open_repository

from instance.models.utils import ValidateModelMixin


# Constants ###################################################################

PROTOCOL_CHOICES = (
    ('http', 'HTTP - Unencrypted clear text'),
    ('https', 'HTTPS - Encrypted'),
)

gandi = GandiAPI()


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Exceptions ##################################################################

class InconsistentInstanceState(Exception):
    """
    Indicates that the status of an instance can't be determined
    """
    pass


# Validators ##################################################################

sha1_validator = RegexValidator(regex='^[0-9a-f]{40}$', message='Full SHA1 hash required')


# Models ######################################################################

class Instance(ValidateModelMixin, TimeStampedModel):
    """
    Instance - Group of servers running an application made of multiple services
    """
    # See `instance.models.server.Server` for a definition of the states
    EMPTY = 'empty'
    NEW = 'new'
    STARTED = 'started'
    ACTIVE = 'active'
    BOOTED = 'booted'
    PROVISIONED = 'provisioned'
    REBOOTING = 'rebooting'
    READY = 'ready'
    LIVE = 'live'
    STOPPING = 'stopping'
    STOPPED = 'stopped'
    TERMINATING = 'terminating'

    sub_domain = models.CharField(max_length=50)
    email = models.EmailField(default='contact@example.com')
    name = models.CharField(max_length=250)

    base_domain = models.CharField(max_length=50, default=settings.INSTANCES_BASE_DOMAIN)
    protocol = models.CharField(max_length=5, default='http', choices=PROTOCOL_CHOICES)

    last_provisioning_started = models.DateTimeField(blank=True, null=True)

    logger = InstanceLoggerAdapter(logger, {})

    class Meta:
        abstract = True
        unique_together = ('base_domain', 'sub_domain')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Ensure we have the right logger
        self.update_logger()

    def __str__(self):
        return '{0.name} ({0.url})'.format(self)

    @property
    def domain(self):
        """
        Instance domain name
        """
        return '{0.sub_domain}.{0.base_domain}'.format(self)

    @property
    def url(self):
        """
        Instance URL
        """
        return u'{0.protocol}://{0.domain}/'.format(self)

    @property
    def active_server_set(self):
        """
        Returns the subset of `self.server_set` which aren't terminated
        """
        return self.server_set.exclude_terminated()

    @property
    def status(self):
        """
        Instance status
        """
        active_server_set = self.active_server_set
        if not active_server_set:
            return self.EMPTY
        elif active_server_set.count() > 1:
            raise InconsistentInstanceState('Multiple servers are active, which is unsupported')
        else:
            return active_server_set[0].status

    @property
    def event_context(self):
        """
        Context dictionary to include in events
        """
        return {'instance_id': self.pk}

    @staticmethod
    def on_post_save(sender, instance, created, **kwargs):
        """
        Triggered by the post_save event, with `created` a boolean indicating if the object was just
        created in the DB
        """
        self = instance
        self.update_logger()

    def update_logger(self):
        """
        Start referencing the instance in logs once the DB entry exist
        """
        if self.pk is not None:
            self.logger = InstanceLoggerAdapter(logger, {'obj': self})

    @property
    def log_text(self):
        """
        Combines the instance and server log outputs in chronological order
        Currently only supports one non-terminated server at a time
        Returned as a text string
        """
        current_server = self.active_server_set.get()
        # TODO: Filter out log entries for which the user doesn't have view rights
        server_log_entry_set = current_server.log_entry_set.order_by('pk')\
                                                           .iterator()
        instance_log_entry_set = self.log_entry_set.order_by('pk')\
                                                   .iterator()

        next_server_log_entry = partial(next, server_log_entry_set, None)
        next_instance_log_entry = partial(next, instance_log_entry_set, None)

        log_text = ''
        instance_log_entry = next_instance_log_entry()
        server_log_entry = next_server_log_entry()

        while instance_log_entry is not None and server_log_entry is not None:
            if server_log_entry.created < instance_log_entry.created:
                log_text += '{}\n'.format(server_log_entry)
                server_log_entry = next_server_log_entry()
            else:
                log_text += '{}\n'.format(instance_log_entry)
                instance_log_entry = next_instance_log_entry()

        while instance_log_entry is not None:
            log_text += '{}\n'.format(instance_log_entry)
            instance_log_entry = next_instance_log_entry()

        while server_log_entry is not None:
            log_text += '{}\n'.format(server_log_entry)
            server_log_entry = next_server_log_entry()

        return log_text


# Git #########################################################################

class GitHubInstanceQuerySet(models.QuerySet):
    """
    Additional methods for instance querysets
    Also used as the standard manager for the GitHubInstance model
    """
    def create(self, *args, **kwargs):
        """
        Augmented `create()` method:
        - Adds support for `fork_name` to allow to set both the github org & repo
        - Sets the github org & repo to `instance.default_fork` if any is missing
        - Sets the `commit_id` to the branch tip if it isn't explicitly passed as an argument
        """
        fork_name = kwargs.pop('fork_name', None)
        instance = self.model(**kwargs)
        if fork_name is None and (not instance.github_organization_name or not instance.github_repository_name):
            fork_name = instance.default_fork
        if fork_name is not None:
            instance.set_fork_name(fork_name, commit=False)
        if not instance.commit_id:
            instance.set_to_branch_tip(commit=False)
        if not instance.name:
            instance.name = instance.reference_name

        self._for_write = True
        instance.save(force_insert=True, using=self.db)
        return instance

    def get(self, *args, **kwargs):
        """
        Augmented `get()` method:
        - Adds support for `fork_name` to allow to query the github org & repo using a single argument
        """
        fork_name = kwargs.pop('fork_name', None)
        if fork_name is not None:
            kwargs['github_organization_name'], kwargs['github_repository_name'] = fork_name2tuple(fork_name)

        return super().get(*args, **kwargs)


class VersionControlInstanceMixin(models.Model):
    """
    Instances linked to a VCS, such as git
    """

    class Meta:
        abstract = True

    branch_name = models.CharField(max_length=50, default='master')
    ref_type = models.CharField(max_length=50, default='heads')
    commit_id = models.CharField(max_length=40, validators=[sha1_validator])

    @property
    def commit_short_id(self):
        """
        Short `commit_id`, limited to 7 characters like on GitHub
        """
        if not self.commit_id:
            return None
        return self.commit_id[:7]


class GitHubInstanceMixin(VersionControlInstanceMixin):
    """
    Instance linked to a GitHub repository
    """
    github_organization_name = models.CharField(max_length=200, db_index=True)
    github_repository_name = models.CharField(max_length=200, db_index=True)
    github_pr_number = models.IntegerField(blank=True, null=True)
    github_admin_organization_name = models.CharField(max_length=200, blank=True,
                                                      default=settings.DEFAULT_ADMIN_ORGANIZATION)

    objects = GitHubInstanceQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def default_fork(self): #pylint: disable=no-self-use
        """
        Name of the fork to use by default, when no repository is specified
        """
        return NotImplementedError

    @property
    def fork_name(self):
        """
        Fork name (eg. 'open-craft/edx-platform')
        """
        return '{0.github_organization_name}/{0.github_repository_name}'.format(self)

    @property
    def github_base_url(self):
        """
        Base GitHub URL of the fork (eg. 'https://github.com/open-craft/edx-platform')
        """
        return 'https://github.com/{0.fork_name}'.format(self)

    @property
    def github_pr_url(self):
        """
        Web URL of the Github PR, or None if the PR number is not set.
        """
        if self.github_pr_number is None:
            return None
        return '{0.github_base_url}/pull/{0.github_pr_number}'.format(self)

    @property
    def github_branch_url(self):
        """
        GitHub URL of the branch tree
        """
        return '{0.github_base_url}/tree/{0.branch_name}'.format(self)

    @property
    def repository_url(self):
        """
        URL of the git repository (eg. 'https://github.com/open-craft/edx-platform.git')
        """
        return '{0.github_base_url}.git'.format(self)

    @property
    def updates_feed(self):
        """
        RSS/Atom feed of commits made on the repository/branch
        """
        return '{0.github_base_url}/commits/{0.branch_name}.atom'.format(self)

    @property
    def github_admin_username_list(self):
        """
        Returns the github usernames of this instance admins

        Admins are the members of the default team of the `github_admin_organization_name` org
        """
        if self.github_admin_organization_name:
            return get_username_list_from_team(self.github_admin_organization_name)
        else:
            return []

    def set_to_branch_tip(self, branch_name=None, ref_type=None, commit=True):
        """
        Set the `commit_id` to the current tip of the branch

        By default, save the instance object - pass `commit=False` to not save it
        """
        if branch_name is not None:
            self.branch_name = branch_name
        if ref_type is not None:
            self.ref_type = ref_type
        self.logger.info('Setting instance to tip of branch %s', self.branch_name)
        new_commit_id = github.get_commit_id_from_ref(
            self.fork_name,
            self.branch_name,
            ref_type=self.ref_type)

        if new_commit_id != self.commit_id:
            old_commit_short_id = self.commit_short_id
            self.commit_id = new_commit_id

            # Update the hash in the instance title if it is present there
            # TODO: Find a better way to handle this - include the hash dynamically?
            # TODO: Figure out why the warnings aren't suppressed despite the fact that it's a mixin
            if self.name and old_commit_short_id: #pylint: disable=access-member-before-definition
                #pylint: disable=attribute-defined-outside-init
                self.name = self.name.replace(old_commit_short_id, self.commit_short_id)

        if commit:
            self.save()

    def set_fork_name(self, fork_name, commit=True):
        """
        Set the organization and repository based on the GitHub fork name

        By default, save the instance object - pass `commit=False` to not save it
        """
        self.logger.info('Setting fork name: %s', fork_name)
        fork_org, fork_repo = github.fork_name2tuple(fork_name)
        if self.github_organization_name == fork_org \
                and self.github_repository_name == fork_repo:
            return

        self.github_organization_name = fork_org
        self.github_repository_name = fork_repo
        if commit:
            self.save()


# Ansible #####################################################################

class AnsibleInstanceMixin(models.Model):
    """
    An instance that relies on Ansible to deploy its services
    """
    ansible_source_repo_url = models.URLField(max_length=256,
                                              default='https://github.com/edx/configuration.git')

    configuration_version = models.CharField(max_length=50, default='master')
    ansible_playbook_name = models.CharField(max_length=50, default='edx_sandbox')
    ansible_extra_settings = models.TextField(blank=True)

    # List of attributes to include in the settings output
    ANSIBLE_SETTINGS = ['ansible_extra_settings']

    class Meta:
        abstract = True

    @property
    def ansible_playbook_filename(self):
        """
        File name of the ansible playbook
        """
        return '{}.yml'.format(self.ansible_playbook_name)

    @property
    def inventory_str(self):
        """
        The ansible inventory (list of servers) as a string
        """
        inventory = ['[app]']
        server_model = self.server_set.model
        for server in self.server_set.filter(status=server_model.BOOTED).order_by('created'):
            inventory.append(server.public_ip)
        inventory_str = '\n'.join(inventory)
        self.logger.debug('Inventory:\n%s', inventory_str)
        return inventory_str

    @property
    def vars_str(self):
        """
        The ansible vars (private configuration) as a string
        """
        template = loader.get_template('instance/ansible/vars.yml')
        vars_str = template.render({'instance': self})
        for attr_name in self.ANSIBLE_SETTINGS:
            additional_vars = getattr(self, attr_name)
            vars_str = ansible.yaml_merge(vars_str, additional_vars)
        self.logger.debug('Vars.yml:\n%s', vars_str)
        return vars_str

    def run_playbook(self):
        """
        Run a playbook against the instance active servers
        """
        with open_repository(self.ansible_source_repo_url,
                             ref=self.configuration_version) as configuration_repo:
            playbook_path = os.path.join(configuration_repo.working_dir, 'playbooks')
            requirements_path = os.path.join(configuration_repo.working_dir, 'requirements.txt')

            self.logger.info('Running playbook "%s/%s"...', playbook_path, self.ansible_playbook_filename)

            log_lines = []
            with ansible.run_playbook(
                requirements_path,
                self.inventory_str,
                self.vars_str,
                playbook_path,
                self.ansible_playbook_filename,
                username=settings.OPENSTACK_SANDBOX_SSH_USERNAME,
            ) as processus:
                for line in processus.stdout:
                    line = line.decode('utf-8').rstrip()
                    self.logger.info(line)
                    log_lines.append([line.rstrip()])

        self.logger.info('Playbook run completed')
        return log_lines


# Open edX ####################################################################

class OpenEdXInstance(AnsibleInstanceMixin, GitHubInstanceMixin, Instance):
    """
    A single instance running a set of Open edX services
    """
    forum_version = models.CharField(max_length=50, default='master')
    notifier_version = models.CharField(max_length=50, default='master')
    xqueue_version = models.CharField(max_length=50, default='master')
    certs_version = models.CharField(max_length=50, default='master')

    s3_access_key = models.CharField(max_length=50, blank=True)
    s3_secret_access_key = models.CharField(max_length=50, blank=True)
    s3_bucket_name = models.CharField(max_length=50, blank=True)

    ANSIBLE_SETTINGS = AnsibleInstanceMixin.ANSIBLE_SETTINGS + ['ansible_s3_settings']

    class Meta:
        verbose_name = 'Open edX Instance'
        ordering = ['-created']

    @property
    def default_fork(self):
        """
        Name of the fork to use by default, when no repository is specified
        """
        return settings.DEFAULT_FORK

    @property
    def reference_name(self):
        """
        A descriptive name for the instance, which includes meaningful attributes
        """
        return '{s.github_organization_name}/{s.branch_name} ({s.commit_short_id})'.format(s=self)

    @property
    def ansible_s3_settings(self):
        """
        Ansible settings for the S3 bucket
        """
        if not self.s3_access_key or not self.s3_secret_access_key or not self.s3_bucket_name:
            return ''

        template = loader.get_template('instance/ansible/s3.yml')
        return template.render({'instance': self})

    @property
    def studio_sub_domain(self):
        """
        Studio sub-domain name (eg. 'studio.master')
        """
        return 'studio.{}'.format(self.sub_domain)

    @property
    def studio_domain(self):
        """
        Studio full domain name (eg. 'studio.master.sandbox.opencraft.com')
        """
        return '{0.studio_sub_domain}.{0.base_domain}'.format(self)

    @property
    def studio_url(self):
        """
        Studio URL
        """
        return u'{0.protocol}://{0.studio_domain}/'.format(self)

    @log_exception
    def provision(self):
        """
        Run the provisioning sequence of the instance, recreating the servers from scratch

        Returns: (server, ansible_log)
        """
        self.last_provisioning_started = timezone.now()
        self.save()

        # Server
        self.logger.info('Terminate servers')
        self.server_set.terminate()
        self.logger.info('Start new server')
        server = self.server_set.create()
        server.start()

        # DNS
        self.logger.info('Waiting for IP assignment on server %s...', server)
        server.sleep_until_status([server.ACTIVE, server.BOOTED])
        self.logger.info('Updating DNS: LMS at %s...', self.domain)
        gandi.set_dns_record(type='A', name=self.sub_domain, value=server.public_ip)
        self.logger.info('Updating DNS: Studio at %s...', self.studio_domain)
        gandi.set_dns_record(type='CNAME', name=self.studio_sub_domain, value=self.sub_domain)

        # Provisioning (ansible)
        self.logger.info('Waiting for SSH to become available on server {}...'.format(server))
        server.sleep_until_status(server.BOOTED)
        ansible_log = self.run_playbook()
        server.update_status(provisioned=True)

        # Reboot
        self.logger.info('Rebooting server %s...', server)
        server.reboot()
        server.sleep_until_status(server.READY)
        self.logger.info('Provisioning completed')

        return (server, ansible_log)

post_save.connect(OpenEdXInstance.on_post_save, sender=OpenEdXInstance)
