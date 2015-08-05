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

import os

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.template import loader
from django_extensions.db.models import TimeStampedModel

from instance import ansible, github
from instance.gandi import GandiAPI
from instance.log_exception import log_exception
from instance.repo import clone_configuration_repo
from instance.models.logging_mixin import LoggerInstanceMixin
from instance.models.utils import ValidateModelMixin


# Constants ###################################################################

PROTOCOL_CHOICES = (
    ('http', 'HTTP - Unencrypted clear text'),
    ('https', 'HTTPS - Encrypted'),
)

gandi = GandiAPI()


# Validators ##################################################################

sha1_validator = RegexValidator(regex='^[0-9a-f]{40}$', message='Full SHA1 hash required')


# Models ######################################################################

class Instance(ValidateModelMixin, TimeStampedModel):
    """
    Instance - Group of servers running an application made of multiple services
    """
    sub_domain = models.CharField(max_length=50, blank=False)
    email = models.EmailField(default='contact@example.com')
    name = models.CharField(max_length=250, blank=False)

    base_domain = models.CharField(max_length=50, default=settings.INSTANCES_BASE_DOMAIN)
    protocol = models.CharField(max_length=5, default='http', choices=PROTOCOL_CHOICES)

    class Meta:
        abstract = True
        unique_together = ('base_domain', 'sub_domain')

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


# Git #########################################################################

class VersionControlInstanceMixin(models.Model):
    """
    Instances linked to a VCS, such as git
    """

    class Meta:
        abstract = True

    branch_name = models.CharField(max_length=50, default='master')
    ref_type = models.CharField(max_length=50, default='heads')
    commit_id = models.CharField(max_length=40, blank=False, validators=[sha1_validator])

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
    github_organization_name = models.CharField(max_length=50, db_index=True, blank=False)
    github_repository_name = models.CharField(max_length=50, db_index=True, blank=False)

    class Meta:
        abstract = True

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

    def set_to_branch_tip(self, branch_name=None, ref_type=None, commit=True):
        """
        Set the `commit_id` to the current tip of the branch
        """
        if branch_name is not None:
            self.branch_name = branch_name
        if ref_type is not None:
            self.ref_type = ref_type
        self.log('info', 'Setting instance {} to tip of branch {}'.format(self, self.branch_name))
        self.commit_id = github.get_commit_id_from_ref(
            self.fork_name,
            self.branch_name,
            ref_type=self.ref_type)
        if commit:
            self.save()

    def set_fork_name(self, fork_name, commit=True):
        """
        Set the organization and repository based on the GitHub fork name
        """
        self.log('info', 'Setting fork name for instance {}: {}'.format(self, fork_name))
        fork_org, fork_repo = github.fork_name2tuple(fork_name)
        if self.github_organization_name != fork_org \
                or self.github_repository_name != fork_repo:
            self.github_organization_name = fork_org
            self.github_repository_name = fork_repo
            if commit:
                self.save()


# Ansible #####################################################################

class AnsibleInstanceMixin(models.Model):
    """
    An instance that relies on Ansible to deploy its services
    """
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
        for server in self.server_set.filter(status='booted').order_by('created'):
            inventory.append(server.public_ip)
        inventory_str = '\n'.join(inventory)
        self.log('debug', 'Inventory for instance {}:\n{}'.format(self, inventory_str))
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
        self.log('debug', 'Vars.yml for instance {}:\n{}'.format(self, vars_str))
        return vars_str

    def run_playbook(self, playbook_name=None):
        """
        Run a playbook against the instance active servers
        """
        configuration_repo_path = clone_configuration_repo()
        playbook_path = os.path.join(configuration_repo_path, 'playbooks')
        requirements_path = os.path.join(configuration_repo_path, 'requirements.txt')

        self.log('info', 'Running playbook "{playbook_path}/{playbook_name}" for instance {instance}...'.format(
            playbook_path=playbook_path,
            playbook_name=playbook_name,
            instance=self,
        ))

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
                self.log('info', line)
                log_lines.append([line.rstrip()])

        return log_lines


# Open edX ####################################################################

class OpenEdXInstance(AnsibleInstanceMixin, GitHubInstanceMixin, LoggerInstanceMixin, Instance):
    """
    A single instance running a set of Open edX services
    """
    s3_access_key = models.CharField(max_length=50, blank=True)
    s3_secret_access_key = models.CharField(max_length=50, blank=True)
    s3_bucket_name = models.CharField(max_length=50, blank=True)

    ANSIBLE_SETTINGS = AnsibleInstanceMixin.ANSIBLE_SETTINGS + ['ansible_s3_settings']

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

    @log_exception
    def run_provisioning(self):
        """
        Run the provisioning sequence of the instance, recreating the servers from scratch
        """
        # Server
        self.log('info', 'Terminate servers for instance {}...'.format(self))
        self.server_set.terminate()
        self.log('info', 'Start new server for instance {}...'.format(self))
        server = self.server_set.create()
        server.start()

        # DNS
        self.log('info', 'Waiting for IP assignment on server {}...'.format(server))
        server.sleep_until_status('active')
        self.log('info', 'Updating DNS for instance {}: LMS at {}...'.format(self, self.domain))
        gandi.set_dns_record(type='A', name=self.sub_domain, value=server.public_ip)
        self.log('info', 'Updating DNS for instance {}: Studio at {}...'.format(self, self.studio_domain))
        gandi.set_dns_record(type='CNAME', name=self.studio_sub_domain, value=self.sub_domain)

        # Ansible
        self.log('info', 'Waiting for SSH to become available on server {}...'.format(server))
        server.sleep_until_status('booted')
        ansible_log = self.run_playbook()

        return (server, ansible_log)
