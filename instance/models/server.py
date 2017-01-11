# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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

import logging
import time

from django.conf import settings
from django.db import models
from django.db.models import Q
from django_extensions.db.models import TimeStampedModel
import novaclient
import requests
from swampdragon.pubsub_providers.data_publisher import publish_data

from instance import openstack
from instance.logging import ModelLoggerAdapter
from instance.models.utils import (
    ValidateModelMixin, ResourceState, ModelResourceStateDescriptor, SteadyStateException
)
from instance.utils import is_port_open, to_json


# Logging #####################################################################

logger = logging.getLogger(__name__)


# States ######################################################################

class ServerState(ResourceState):
    """
    A [finite state machine] state describing a virtual machine.
    """
    # A state is "steady" if we don't expect it to change.
    # This information can be used to:
    # - delay execution of an operation until the target server reaches a steady state
    # - raise an exception when trying to schedule an operation that depends on a state change
    #   while the target server is in a steady state
    # Steady states include: Status.BuildFailed, Status.Ready, Status.Terminated
    is_steady_state = False

    # A server accepts SSH commands if it has Status.Ready.
    # This information can be used to delay execution of an operation
    # until the target server has reached this status.
    accepts_ssh_commands = False

    # We know that a VM is available if a server has Status.Booting or Status.Ready.
    # This information can be used to delay execution of an operation
    # until the target server has reached one of these statuses.
    vm_available = False


class Status(ResourceState.Enum):
    """
    The states that a server can be in.
    """
    class Pending(ServerState):
        """ Not yet loaded (need to request new VM) """
        state_id = 'pending'

    class Building(ServerState):
        """ Building new VM from image """
        state_id = 'building'

    class Booting(ServerState):
        """ (Re-)Booting """
        state_id = 'booting'
        vm_available = True

    class Ready(ServerState):
        """ Booted and ready """
        state_id = 'ready'
        is_steady_state = True
        accepts_ssh_commands = True
        vm_available = True

    class Terminated(ServerState):
        """ Stopped forever """
        state_id = 'terminated'
        is_steady_state = True

    class Unknown(ServerState):
        """ OpenStack API is not responsive """
        state_id = 'unknown'

    class BuildFailed(ServerState):
        """ OpenStack failed to create the VM """
        state_id = 'failed'
        name = 'Build failed'
        is_steady_state = True


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
        qs = self.filter(~Q(_status=Status.Terminated.state_id), *args, **kwargs)
        for server in qs:
            server.terminate()
        return qs

    def exclude_terminated(self):
        """
        Filter out terminated servers from the queryset
        """
        return self.filter(~Q(_status=Status.Terminated.state_id))


class Server(ValidateModelMixin, TimeStampedModel):
    """
    A single server VM
    """
    name_prefix = models.SlugField(max_length=20, blank=False)

    Status = Status
    status = ModelResourceStateDescriptor(
        state_classes=Status.states, default_state=Status.Pending, model_field_name='_status'
    )
    _status = models.CharField(
        max_length=20,
        default=status.default_state_class.state_id,
        choices=status.model_field_choices,
        db_index=True,
        db_column='status',
    )
    # State transitions:
    _status_to_building = status.transition(from_states=(Status.Pending, Status.Unknown), to_state=Status.Building)
    _status_to_build_failed = status.transition(
        from_states=(Status.Building, Status.Unknown), to_state=Status.BuildFailed
    )
    _status_to_booting = status.transition(
        from_states=(Status.Building, Status.Ready, Status.Unknown), to_state=Status.Booting
    )
    _status_to_ready = status.transition(from_states=(Status.Booting, Status.Unknown), to_state=Status.Ready)
    _status_to_terminated = status.transition(to_state=Status.Terminated)
    _status_to_unknown = status.transition(
        from_states=(Status.Building, Status.Booting, Status.Ready), to_state=Status.Unknown
    )

    objects = ServerQuerySet().as_manager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ModelLoggerAdapter(logger, {'obj': self})

    @property
    def name(self):
        """ Get a name for this server (slug-friendly) """
        assert self.id is not None
        return "{prefix}-{num}".format(prefix=self.name_prefix, num=self.id)

    @property
    def event_context(self):
        """
        Context dictionary to include in events
        """
        return {'server_id': self.pk}

    def get_log_message_annotation(self):
        """
        Format a log line annotation for this server.
        """
        return 'server={} ({!s:.20})'.format(self.pk, self.name)

    def sleep_until(self, condition, timeout=3600):
        """
        Sleep in a loop until condition related to server status is fulfilled,
        or until timeout (provided in seconds) is reached.

        Raises an exception if the desired condition can not be fulfilled.
        This can happen if the server is in a steady state (i.e., a state that is not expected to change)
        that does not fulfill the desired condition.

        The default timeout is 1h.

        Use as follows:

            server.sleep_until(lambda: server.status.is_steady_state)
            server.sleep_until(lambda: server.status.accepts_ssh_commands)
        """
        # Check if we received a valid timeout value
        # to avoid the possibility of entering an infinite loop (if timeout is negative)
        # or reaching the timeout right away (if timeout is zero)
        assert timeout > 0, "Timeout must be greater than 0 to be able to do anything useful"

        self.logger.info('Waiting to reach status from which we can proceed...')

        while timeout > 0:
            self.update_status()
            if condition():
                self.logger.info(
                    'Reached appropriate status ({name}). Proceeding.'.format(name=self.status.name)
                )
                return
            else:
                if self.status.is_steady_state:
                    raise SteadyStateException(
                        "The current status ({name}) does not fulfill the desired condition "
                        "and is not expected to change.".format(name=self.status.name)
                    )
            time.sleep(1)
            timeout -= 1

        # If we get here, this means we've reached the timeout
        raise TimeoutError(
            "Waited {minutes:.2f} to reach appropriate status, and got nowhere. "
            "Aborting with a status of {status}.".format(minutes=timeout / 60, status=self.status.name)
        )

    def save(self, *args, **kwargs):
        """
        Save this Server
        """
        super().save(*args, **kwargs)
        publish_data('notification', {
            'type': 'server_update',
            'server_pk': self.pk,
        })

    def update_status(self):
        """
        Check the current status and update it if it has changed
        """
        raise NotImplementedError


class OpenStackServer(Server):
    """
    A Server VM hosted on an OpenStack cloud
    """
    openstack_id = models.CharField(max_length=250, db_index=True, blank=True)

    class Meta:
        verbose_name = 'OpenStack VM'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nova = openstack.get_nova_client()

    def __str__(self):
        if self.openstack_id:
            return self.openstack_id
        else:
            return 'Pending OpenStack Server'

    @property
    def os_server(self):
        """
        OpenStack nova server API endpoint
        """
        if not self.openstack_id:
            assert self.status == Status.Pending
            self.start()
        return self.nova.servers.get(self.openstack_id)

    @property
    def public_ip(self):
        """
        Return one of the public address(es)
        """
        if not self.openstack_id:
            return None

        try:
            public_addr = openstack.get_server_public_address(self.os_server)
        except (requests.RequestException, novaclient.exceptions.ClientException):
            return None  # Could not determine an IP based on the OS API
        if not public_addr:
            return None

        return public_addr['addr']

    @property
    def vm_created(self):
        """
        Return True if this server has a VM, False otherwise
        """
        return self.status.vm_available or (self.status == Status.Building and self.openstack_id)

    @property
    def vm_not_yet_requested(self):
        """
        Return True if the VM has not been requested, and name_prefix can be changed.
        """
        return self.status == Status.Pending

    def update_status(self):
        """
        Refresh the status by querying the openstack server via nova
        """
        # TODO: Check when server is stopped or terminated

        # First check if it makes sense to update the current status.
        # This is not the case if we can not interact with the server:
        if self.status in (Status.BuildFailed, Status.Terminated):
            return self.status
        try:
            os_server = self.os_server
        except (requests.RequestException, novaclient.exceptions.ClientException):
            self.logger.debug('Could not reach the OpenStack API')
            if self.status not in (Status.BuildFailed, Status.Terminated, Status.Pending, Status.Unknown):
                self._status_to_unknown()
            return self.status
        self.logger.debug('Updating status from nova (currently %s):\n%s', self.status, to_json(os_server))

        if self.status == Status.Unknown:
            if os_server.status in ('INITIALIZED', 'BUILDING'):
                # OpenStack has multiple API versions; INITIALIZED is current; BUILDING was used in the past
                self._status_to_building()

        if self.status in (Status.Building, Status.Unknown):
            self.logger.debug('OpenStack: loaded="%s" status="%s"', os_server._loaded, os_server.status)
            if os_server._loaded and os_server.status == 'ACTIVE':
                self._status_to_booting()

        if self.status in (Status.Booting, Status.Unknown) and self.public_ip and is_port_open(self.public_ip, 22):
            self._status_to_ready()

        return self.status

    @Server.status.only_for(Status.Pending)
    def start(self, **kwargs):
        """
        Get a server instance started and an openstack_id assigned

        TODO: Add handling of quota limitations & waiting list
        TODO: Create the key dynamically
        """
        self.logger.info('Starting server (status=%s)...', self.status)
        self._status_to_building()
        try:
            os_server = openstack.create_server(
                self.nova,
                self.name,
                settings.OPENSTACK_SANDBOX_FLAVOR,
                settings.OPENSTACK_SANDBOX_BASE_IMAGE,
                key_name=settings.OPENSTACK_SANDBOX_SSH_KEYNAME,
                **kwargs
            )
        except novaclient.exceptions.ClientException as e:
            self.logger.error('Failed to start server: %s', e)
            self._status_to_build_failed()
        else:
            self.openstack_id = os_server.id
            self.logger.info('Server got assigned OpenStack id %s', self.openstack_id)
            # Persist OpenStack ID
            self.save()

    @Server.status.only_for(Status.Ready, Status.Booting)
    def reboot(self, reboot_type='SOFT'):
        """
        Reboot the server

        This requires to switch the status to 'booting'.
        If the current state doesn't allow to switch to this status,
        a WrongStateException exception is thrown.
        """
        if self.status == Status.Booting:
            return
        self._status_to_booting()
        self.os_server.reboot(reboot_type=reboot_type)

        # TODO: Find a better way to wait for the server shutdown and reboot
        # Currently, without sleeping here, the status would immediately switch back to ready,
        # as SSH is still available until the reboot terminates the SSHD process
        time.sleep(30)

    def terminate(self):
        """
        Terminate the server
        """
        self.logger.info('Terminating server (status=%s)...', self.status)
        if self.status == Status.Terminated:
            return
        elif not self.vm_created:
            self._status_to_terminated()
            return

        self._status_to_terminated()
        try:
            self.os_server.delete()
        except novaclient.exceptions.NotFound:
            self.logger.error('Error while attempting to terminate server: could not find OS server')
