"""
Instance app models - Instance
"""
#pylint: disable=no-init


# Imports #####################################################################

from swampdragon.pubsub_providers.data_publisher import publish_data

from django.conf import settings
from django.db import models
from django.template import loader
from django_extensions.db.models import TimeStampedModel

from .. import ansible
from ..gandi import GandiAPI


# Constants ###################################################################

PROTOCOL_CHOICES = (
    ('http', 'HTTP - Unencrypted clear text'),
    ('https', 'HTTPS - Encrypted'),
)

gandi = GandiAPI()


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Models ######################################################################

class Instance(TimeStampedModel):
    '''
    Instance - Group of servers running an application made of multiple services
    '''
    sub_domain = models.CharField(max_length=50, blank=False)
    email = models.EmailField(default='contact@example.com')
    name = models.CharField(max_length=50, blank=False)

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
    commit_id = models.CharField(max_length=40, default='master')


class GitHubInstanceMixin(VersionControlInstanceMixin):
    '''
    Instance linked to a GitHub repository
    '''
    GITHUB_DEFAULT_ORG = 'open-craft'
    GITHUB_DEFAULT_REPO = 'opencraft'

    github_organization_name = models.CharField(max_length=50, db_index=True, default=GITHUB_DEFAULT_ORG)
    github_repository_name = models.CharField(max_length=50, db_index=True, default=GITHUB_DEFAULT_REPO)

    class Meta:
        abstract = True

    @property
    def github_base_url(self):
        return 'https://github.com/{0.github_organization_name}/{0.github_repository_name}'.format(self)

    @property
    def repository_url(self):
        return '{0.github_base_url}.git'.format(self)

    @property
    def updates_feed(self):
        return '{0.github_base_url}/commits/{0.branch_name}.atom'.format(self)


# Ansible #####################################################################

class AnsibleInstanceMixin(models.Model):
    '''
    An instance that relies on Ansible to deploy its services
    '''
    ansible_playbook = models.CharField(max_length=50, blank=False)

    class Meta:
        abstract = True

    @property
    def inventory_str(self):
        '''
        The ansible inventory (list of servers) as a string
        '''
        inventory = ['[app]']
        for server in self.server_set.filter(status='booted'):
            inventory.append(server.public_ip)
        inventory_str = '\n'.join(inventory)
        logger.debug('Inventory for instance %s:\n%s', self, inventory_str)
        return inventory_str

    @property
    def vars_str(self):
        '''
        The ansible vars (private configuration) as a string
        '''
        template = loader.get_template('instance/ansible/vars.yml')
        vars_str = template.render({'instance': self})
        logger.debug('Vars.yml for instance %s:\n%s', self, vars_str)
        return vars_str

    def run_playbook(self):
        logger.info('Running playbook "%s" for instance %s...', self.ansible_playbook, self)
        log_lines = []
        with ansible.run_playbook(
            self.inventory_str,
            self.vars_str,
            '{}.yml'.format(self.ansible_playbook),
            username=settings.OPENSTACK_SANDBOX_SSH_USERNAME,
        ) as processus:
            for line in processus.stdout:
                line = line.decode('utf-8')
                logger.info(line.rstrip())
                log_lines.append([line.rstrip()])

                publish_data('log', {
                    'type': 'instance_ansible_log',
                    'instance_pk': self.pk,
                    'log_entry': line,
                })

        return log_lines


# Open edX ####################################################################

class OpenEdXInstance(AnsibleInstanceMixin, GitHubInstanceMixin, Instance):
    '''
    A single instance running a set of Open edX services
    '''
    GITHUB_DEFAULT_ORG = 'edx'
    GITHUB_DEFAULT_REPO = 'edx-platform'

    def run_provisioning(self):
        # Server
        logger.info('Terminate servers for instance %s...', self)
        self.server_set.terminate()
        logger.info('Start new server for instance %s...', self)
        server = self.server_set.create()
        server.start()

        # DNS
        logger.info('Waiting for IP assignment on server %s...', server)
        server.sleep_until_status('active')
        logger.info('Updating DNS for instance %s...', self)
        gandi.set_dns_record(type='A', name=self.sub_domain, value=server.public_ip)

        # Ansible
        logger.info('Waiting for SSH to become available on server %s...', server)
        server.sleep_until_status('booted')
        ansible_log = self.run_playbook()

        return (server, ansible_log)
