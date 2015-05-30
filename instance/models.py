"""
Instance app models
"""
#pylint: disable=no-init


# Imports #####################################################################

import novaclient
import time

from pprint import pformat
from swampdragon.pubsub_providers.data_publisher import publish_data

from django.conf import settings
from django.db.models.signals import post_save
from django.db import models
from django.db.models import Q, query
from django.template import loader
from django_extensions.db.models import TimeStampedModel

from . import ansible, openstack
from .gandi import GandiAPI
from .utils import is_port_open


# Constants ###################################################################

PROTOCOL_CHOICES = (
    ('http', 'HTTP - Unencrypted clear text'),
    ('https', 'HTTPS - Encrypted'),
)

SERVER_STATUS_CHOICES = (
    ('new', 'New - Not yet loaded'),
    ('started', 'Started - Running but not active yet'),
    ('active', 'Active - Running but not booted yet'),
    ('booted', 'Booted - Booted but not ready to be added to the application'),
    ('ready', 'Ready - Ready to be added to the application'),
    ('live', 'Live - Is actively used in the application and/or accessed by users'),
    ('stopping', 'Stopping - Stopping temporarily'),
    ('stopped', 'Stopped - Stopped temporarily'),
    ('terminating', 'Terminating - Stopping forever'),
    ('terminated', 'Terminated - Stopped forever'),
)

gandi = GandiAPI()


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Models ######################################################################

###############################################################################
# Server ######################################################################

class ServerQuerySet(query.QuerySet):
    '''
    Additional methods for server querysets
    Also used as the standard manager for the Server model (`Server.objects`)
    '''
    def terminate(self, *args, **kwargs):
        qs = self.filter(~Q(status='terminated'), *args, **kwargs)
        for server in qs:
            server.terminate()
        return qs


class Server(TimeStampedModel):
    '''
    A single server VM
    '''
    status = models.CharField(max_length=10, default='new', choices=SERVER_STATUS_CHOICES, db_index=True)

    objects = ServerQuerySet().as_manager()

    class Meta:
        abstract = True

    def _set_status(self, status):
        self.status = status
        logger.info('Changed status for %s: %s', self, self.status)
        self.save()
        return self.status

    def sleep_until_status(self, target_status):
        logger.info('Waiting for server %s to reach the %s status...', self, target_status)
        while True:
            self.update_status()
            if self.status == target_status:
                break
            time.sleep(1)
        return self.status


class OpenStackServer(Server):
    '''
    A Server VM hosted on an OpenStack cloud
    '''
    instance = models.ForeignKey('OpenEdXInstance', related_name='server_set')
    openstack_id = models.CharField(max_length=250, db_index=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nova = openstack.get_nova_client()

    def __str__(self):
        if self.openstack_id:
            return self.openstack_id
        else:
            return 'New OpenStack Server'

    @property
    def os_server(self):
        if not self.openstack_id:
            assert self.status == 'new'
            self.start()
        return self.nova.servers.get(self.openstack_id)

    @property
    def public_ip(self):
        '''
        Return one of the public address(es)
        '''
        if not self.openstack_id:
            return None

        public_addr = openstack.get_server_public_address(self.os_server)
        if not public_addr:
            return None

        return public_addr['addr']

    def update_status(self):
        '''
        Refresh the status by querying the openstack server via nova

        TODO: Check when server is stopped or terminated
        '''
        # Ensure the 'started' mode by getting the server instance from openstack
        os_server = self.os_server
        logger.debug('Updating status for %s from nova (currently %s):\n%s',
                     self, self.status, pformat(os_server.__dict__))

        if self.status == 'started':
            #pylint: disable=protected-access
            logger.debug('Server %s: loaded="%s" status="%s"', self, os_server._loaded, os_server.status)
            if os_server._loaded and os_server.status == 'ACTIVE':
                self._set_status('active')

        if self.status == 'active':
            if is_port_open(self.public_ip, 22):
                self._set_status('booted')

        return self.status

    def start(self):
        '''
        Get a server instance started and an openstack_id assigned

        TODO: Add handling of quota limitations & waiting list
        TODO: Create the key dynamically
        '''
        logger.info('Starting server %s (status=%s)...', self, self.status)
        if self.status == 'new':
            os_server = openstack.create_server(self.nova,
                self.instance.sub_domain,
                settings.OPENSTACK_SANDBOX_FLAVOR,
                settings.OPENSTACK_SANDBOX_BASE_IMAGE,
                key_name=settings.OPENSTACK_SANDBOX_SSH_KEYNAME,
            )
            self.openstack_id = os_server.id
            logger.info('Server %s got assigned OpenStack id %s', self, self.openstack_id)
            self._set_status('started')
        else:
            raise NotImplementedError

    def terminate(self):
        logger.info('Terminating server %s (status=%s)...', self, self.status)
        if self.status == 'terminated':
            return
        elif self.status == 'new':
            self._set_status('terminated')
            return

        try:
            self.os_server.delete()
        except novaclient.exceptions.NotFound:
            logger.exception('Error while attempting to terminate server %s: could not find OS server', self)

        self._set_status('terminated')

    @staticmethod
    def on_post_save(sender, instance, created, **kwargs):
        publish_data('notification', {
            'type': 'server_update',
            'server_pk': instance.pk,
        })

post_save.connect(OpenStackServer.on_post_save, sender=OpenStackServer)


###############################################################################
# Instance ####################################################################

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
                line = line.rstrip()
                logger.info(line)
                log_lines.append([line])

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
