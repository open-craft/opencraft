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
Instance app models - Server
"""

# Imports #####################################################################

import novaclient
import time

from swampdragon.pubsub_providers.data_publisher import publish_data

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django_extensions.db.models import TimeStampedModel

from instance import openstack
from instance.utils import is_port_open, to_json
from instance.models.instance import OpenEdXInstance
from instance.models.logging_mixin import LoggerMixin
from instance.models.utils import ValidateModelMixin


# Constants ###################################################################

SERVER_STATUS_CHOICES = (
    ('new', 'New - Not yet loaded'),
    ('started', 'Started - Running but not active yet'),
    ('active', 'Active - Running but not booted yet'),
    ('booted', 'Booted - Booted but not ready to be added to the application'),
    ('provisioned', 'Provisioned - Provisioning is completed'),
    ('rebooting', 'Rebooting - Reboot in progress, to apply changes from provisioning'),
    ('ready', 'Ready - Rebooted and ready to add to the application'),
    ('live', 'Live - Is actively used in the application and/or accessed by users'),
    ('stopping', 'Stopping - Stopping temporarily'),
    ('stopped', 'Stopped - Stopped temporarily'),
    ('terminating', 'Terminating - Stopping forever'),
    ('terminated', 'Terminated - Stopped forever'),
)


# Exceptions ##################################################################

class ServerNotReady(Exception):
    """
    Raised when an action is attempted in a status that doesn't allow it
    """
    pass


# Models ######################################################################

class ServerQuerySet(models.QuerySet):
    """
    Additional methods for server querysets
    Also used as the standard manager for the Server model (`Server.objects`)
    """
    def terminate(self, *args, **kwargs):
        """
        Terminate the servers from the queryset
        """
        qs = self.filter(~Q(status='terminated'), *args, **kwargs)
        for server in qs:
            server.terminate()
        return qs

    def exclude_terminated(self):
        """
        Filter out terminated servers from the queryset
        """
        return self.filter(~Q(status='terminated'))


class Server(ValidateModelMixin, TimeStampedModel, LoggerMixin):
    """
    A single server VM
    """
    status = models.CharField(max_length=11, default='new', choices=SERVER_STATUS_CHOICES, db_index=True)

    objects = ServerQuerySet().as_manager()

    class Meta:
        abstract = True

    def _set_status(self, status):
        """
        Update the current status variable, to be called when a status change is detected
        """
        self.status = status
        self.log('info', 'Changed status for {}: {}'.format(self, self.status))
        self.save()
        return self.status

    def sleep_until_status(self, target_status):
        """
        Sleep in a loop until the server reaches one of the specified status
        """
        target_status_list = [target_status] if isinstance(target_status, str) else target_status
        self.log('info', 'Waiting for server {} to reach status {}...'.format(self, target_status_list))

        while True:
            self.update_status()
            if self.status in target_status:
                break
            time.sleep(1)
        return self.status

    @staticmethod
    def on_post_save(sender, instance, created, **kwargs):
        """
        Called when an instance is saved
        """
        publish_data('notification', {
            'type': 'server_update',
            'server_pk': instance.pk,
        })

    def update_status(self, provisioned=False, rebooting=False):
        """
        Check the current status and update it if it has changed
        """
        raise NotImplementedError


class OpenStackServer(Server):
    """
    A Server VM hosted on an OpenStack cloud
    """
    instance = models.ForeignKey(OpenEdXInstance, related_name='server_set')
    openstack_id = models.CharField(max_length=250, db_index=True, blank=True)

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
        """
        OpenStack nova server API endpoint
        """
        if not self.openstack_id:
            assert self.status == 'new'
            self.start()
        return self.nova.servers.get(self.openstack_id)

    @property
    def public_ip(self):
        """
        Return one of the public address(es)
        """
        if not self.openstack_id:
            return None

        public_addr = openstack.get_server_public_address(self.os_server)
        if not public_addr:
            return None

        return public_addr['addr']

    def update_status(self, provisioned=False, rebooting=False):
        """
        Refresh the status by querying the openstack server via nova
        """
        # TODO: Check when server is stopped or terminated
        os_server = self.os_server
        self.log('debug', 'Updating status for {} from nova (currently {}):\n{}'.format(
            self, self.status, to_json(os_server)))

        if self.status == 'started':
            self.log('debug', 'Server {}: loaded="{}" status="{}"'.format(
                self, os_server._loaded, os_server.status))
            if os_server._loaded and os_server.status == 'ACTIVE':
                self._set_status('active')

        elif self.status == 'active' and is_port_open(self.public_ip, 22):
            self._set_status('booted')

        elif self.status == 'booted' and provisioned:
            self._set_status('provisioned')

        elif self.status in ('provisioned', 'ready') and rebooting:
            self._set_status('rebooting')

        elif self.status == 'rebooting' and not rebooting and is_port_open(self.public_ip, 22):
            self._set_status('ready')

        return self.status

    def start(self):
        """
        Get a server instance started and an openstack_id assigned

        TODO: Add handling of quota limitations & waiting list
        TODO: Create the key dynamically
        """
        self.log('info', 'Starting server {} (status={})...'.format(self, self.status))
        if self.status == 'new':
            os_server = openstack.create_server(
                self.nova,
                self.instance.sub_domain,
                settings.OPENSTACK_SANDBOX_FLAVOR,
                settings.OPENSTACK_SANDBOX_BASE_IMAGE,
                key_name=settings.OPENSTACK_SANDBOX_SSH_KEYNAME,
            )
            self.openstack_id = os_server.id
            self.log('info', 'Server {} got assigned OpenStack id {}'.format(self, self.openstack_id))
            self._set_status('started')
        else:
            raise NotImplementedError

    def reboot(self, reboot_type='SOFT'):
        """
        Reboot the server

        This requires to switch the status to 'rebooting', which is first attempted via the
        `update_status` method. If the current state doesn't allow to switch to this status,
        a ServerNotReady exception is thrown.
        """
        if self.update_status(rebooting=True) != 'rebooting':
            raise ServerNotReady("Can't change status to 'rebooting' (current: '{}')".format(self.status))
        self.os_server.reboot(reboot_type=reboot_type)

        # TODO: Find a better way to wait for the server shutdown and reboot
        # Currently, without sleeping here, the status would immediately switch back to ready,
        # as SSH is still available until the reboot terminates the SSHD process
        time.sleep(30)

    def terminate(self):
        """
        Terminate the server
        """
        self.log('info', 'Terminating server {} (status={})...'.format(self, self.status))
        if self.status == 'terminated':
            return
        elif self.status == 'new':
            self._set_status('terminated')
            return

        try:
            self.os_server.delete()
        except novaclient.exceptions.NotFound:
            self.log('exception', 'Error while attempting to terminate server {}: '
                                  'could not find OS server'.format(self))
        finally:
            self._set_status('terminated')

post_save.connect(Server.on_post_save, sender=OpenStackServer)
