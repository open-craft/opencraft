"""
Instance app models - Instance
"""
#pylint: disable=no-init


# Imports #####################################################################

import os

from django.conf import settings
from django.db import models
from django.template import loader
from django_extensions.db.models import TimeStampedModel

from .. import ansible, github
from ..gandi import GandiAPI
from .logging import LoggerInstanceMixin


# Constants ###################################################################

PROTOCOL_CHOICES = (
    ('http', 'HTTP - Unencrypted clear text'),
    ('https', 'HTTPS - Encrypted'),
)

gandi = GandiAPI()


# Models ######################################################################

class Instance(TimeStampedModel):
    '''
    Instance - Group of servers running an application made of multiple services
    '''
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
        return '{0.sub_domain}.{0.base_domain}'.format(self)

    @property
    def url(self):
        return u'{0.protocol}://{0.domain}/'.format(self)


# Git #########################################################################

class VersionControlInstanceMixin(models.Model):
    '''
    Instances linked to a VCS, such as git
    '''

    class Meta:
        abstract = True

    branch_name = models.CharField(max_length=50, default='master')
    commit_id = models.CharField(max_length=40, blank=False)

    @property
    def commit_short_id(self):
        if not self.commit_id:
            return ''
        return self.commit_id[:7]


class GitHubInstanceMixin(VersionControlInstanceMixin):
    '''
    Instance linked to a GitHub repository
    '''
    github_organization_name = models.CharField(max_length=50, db_index=True, blank=False)
    github_repository_name = models.CharField(max_length=50, db_index=True, blank=False)

    class Meta:
        abstract = True

    @property
    def fork_name(self):
        return '{0.github_organization_name}/{0.github_repository_name}'.format(self)

    @property
    def github_base_url(self):
        return 'https://github.com/{0.fork_name}'.format(self)

    @property
    def repository_url(self):
        return '{0.github_base_url}.git'.format(self)

    @property
    def updates_feed(self):
        return '{0.github_base_url}/commits/{0.branch_name}.atom'.format(self)

    def set_to_branch_tip(self, branch_name=None, commit=True):
        if branch_name is not None:
            self.branch_name = branch_name
        self.log('info', 'Setting instance {} to tip of branch {}'.format(self, self.branch_name))
        self.commit_id = github.get_commit_id_from_ref(self.fork_name, self.branch_name)
        if commit:
            self.save()

    def set_fork_name(self, fork_name, branch_name=None, commit=True):
        if branch_name is not None:
            self.branch_name = branch_name
        self.log('info', 'Setting fork name for instance {}: {}/{}'.format(self, fork_name, branch_name))
        fork_org, fork_repo = github.fork_name2tuple(fork_name)
        if self.github_organization_name != fork_org \
                or self.github_repository_name != fork_repo \
                or self.branch_name != branch_name:
            self.github_organization_name = fork_org
            self.github_repository_name = fork_repo
            self.set_to_branch_tip(branch_name=branch_name, commit=False)
            if commit:
                self.save()


# Ansible #####################################################################

class AnsibleInstanceMixin(models.Model):
    '''
    An instance that relies on Ansible to deploy its services
    '''
    ansible_playbook_name = models.CharField(max_length=50, default='edx_sandbox')
    ansible_extra_settings = models.TextField(blank=True)

    # List of attributes to include in the settings output
    ANSIBLE_SETTINGS = ['ansible_extra_settings']

    class Meta:
        abstract = True

    @property
    def ansible_playbook_filename(self):
        return '{}.yml'.format(self.ansible_playbook_name)

    @property
    def inventory_str(self):
        '''
        The ansible inventory (list of servers) as a string
        '''
        inventory = ['[app]']
        for server in self.server_set.filter(status='booted'):
            inventory.append(server.public_ip)
        inventory_str = '\n'.join(inventory)
        self.log('debug', 'Inventory for instance {}:\n{}'.format(self, inventory_str))
        return inventory_str

    @property
    def vars_str(self):
        '''
        The ansible vars (private configuration) as a string
        '''
        template = loader.get_template('instance/ansible/vars.yml')
        vars_str = template.render({'instance': self})
        for attr_name in self.ANSIBLE_SETTINGS:
            vars_str += '\n\n# Settings: {attr_name}\n{settings_str}'.format(
                    attr_name=attr_name,
                    settings_str=getattr(self, attr_name, '')
                )
        self.log('debug', 'Vars.yml for instance {}:\n{}'.format(self, vars_str))
        return vars_str

    def run_playbook(self, playbook_path=None):
        if playbook_path is None:
            playbook_path = os.path.join(settings.CONFIGURATION_REPO_PATH, 'playbooks')

        self.log('info', 'Running playbook "{playbook_path}/{playbook_name}" for instance {instance}...'.format(
            playbook_path=playbook_path,
            playbook_name=self.ansible_playbook_name,
            instance=self,
        ))

        log_lines = []
        with ansible.run_playbook(
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
    '''
    A single instance running a set of Open edX services
    '''
    s3_access_key = models.CharField(max_length=50, blank=True)
    s3_secret_access_key = models.CharField(max_length=50, blank=True)
    s3_bucket_name = models.CharField(max_length=50, blank=True)

    ANSIBLE_SETTINGS = AnsibleInstanceMixin.ANSIBLE_SETTINGS + ['ansible_s3_settings']

    @property
    def ansible_s3_settings(self):
        if not self.s3_access_key or not self.s3_secret_access_key or not self.s3_bucket_name:
            return ''

        template = loader.get_template('instance/ansible/s3.yml')
        return template.render({'instance': self})

    def run_provisioning(self):
        # Server
        self.log('info', 'Terminate servers for instance {}...'.format(self))
        self.server_set.terminate()
        self.log('info', 'Start new server for instance {}...'.format(self))
        server = self.server_set.create()
        server.start()

        # DNS
        self.log('info', 'Waiting for IP assignment on server {}...'.format(server))
        server.sleep_until_status('active')
        self.log('info', 'Updating DNS for instance {}...'.format(self))
        gandi.set_dns_record(type='A', name=self.sub_domain, value=server.public_ip)

        # Ansible
        self.log('info', 'Waiting for SSH to become available on server {}...'.format(server))
        server.sleep_until_status('booted')
        ansible_log = self.run_playbook()

        return (server, ansible_log)
