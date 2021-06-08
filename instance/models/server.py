# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
import subprocess
import time

from django.conf import settings
from django.db import models
from django.db.models import Q
from django_extensions.db.models import TimeStampedModel
import novaclient
import requests

from instance import openstack_utils
from instance.logging import ModelLoggerAdapter
from instance.models.utils import (
    ValidateModelMixin, ResourceState, ModelResourceStateDescriptor, SteadyStateException, default_setting
)
from instance.utils import is_port_open, to_json, publish_data


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

    # We can only reconfigure the load balancer in case the server is in Status.Ready.
    # This field is to be set just in the Ready state and False in other states.
    is_healthy_state = False


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
        is_healthy_state = True

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
    name_prefix = models.SlugField(max_length=30, blank=False)

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

    def sleep_until(self, condition, timeout=3600, steady_state_check=True):
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
        initial_timeout = timeout

        self.logger.info('Waiting to reach status from which we can proceed...')

        while timeout > 0:
            self.update_status()
            if condition():
                self.logger.info(
                    'Reached appropriate status ({name}). Proceeding.'.format(name=self.status.name)
                )
                return
            else:
                if steady_state_check and self.status.is_steady_state:
                    raise SteadyStateException(
                        "The current status ({name}) does not fulfill the desired condition "
                        "and is not expected to change.".format(name=self.status.name)
                    )
            time.sleep(1)
            timeout -= 1

        # If we get here, this means we've reached the timeout
        raise TimeoutError(
            "Waited {minutes:.2f} minutes to reach appropriate status, and got nowhere. "
            "Aborting with a status of {status}.".format(minutes=initial_timeout / 60, status=self.status.name)
        )

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        Save this server.
        """
        super().save(*args, **kwargs)
        publish_data({
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
    openstack_region = models.CharField(
        max_length=16,
        blank=False,
        default=default_setting('OPENSTACK_REGION'),
    )
    openstack_id = models.CharField(max_length=250, db_index=True, blank=True)
    _public_ip = models.GenericIPAddressField(blank=True, null=True, db_column="public_ip")

    class Meta:
        verbose_name = 'OpenStack VM'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nova = openstack_utils.get_nova_client(self.openstack_region)

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
        if not self.vm_created:
            # No VM means no public IP.
            return None
        if not self._public_ip:
            # This branch will only be reached the first time the public IP address of a server is
            # requested. We let any exceptions occurring during the Nova API calls propagate to the
            # caller.  We previously caught and ignored all exceptions here, which led to
            # hard-to-debug bugs.
            public_addr = openstack_utils.get_server_public_address(self.os_server)
            if not public_addr:
                return None
            self._public_ip = public_addr['addr']
            self.save()
        return self._public_ip

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

    def _update_status_from_nova(self, os_server):
        """
        Update the status from the Nova Server object given in os_server.
        """
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

    def update_status(self):
        """
        Refresh the status by querying the openstack server via nova
        """
        # TODO: Check when server is stopped

        # First check if it makes sense to update the current status.
        # This is not the case if we can not interact with the server:
        if self.status not in [Status.BuildFailed, Status.Terminated, Status.Pending]:
            try:
                os_server = self.os_server
            except novaclient.exceptions.NotFound:
                # This exception is raised before the server is created, and after it has been
                # terminated.  Because of the first "if", we can't get her in Pending state, so the
                # server must have been terminated.
                self.logger.debug('Server does not exist anymore: %s', self)
                self._status_to_terminated()
            except (requests.RequestException, novaclient.exceptions.ClientException) as exc:
                self.logger.debug('Could not reach the OpenStack API due to %s', exc)
                if self.status != Status.Unknown:
                    self._status_to_unknown()
            else:
                self._update_status_from_nova(os_server)
        return self.status

    @Server.status.only_for(Status.Pending)
    def start(self,
              flavor_selector=settings.OPENSTACK_SANDBOX_FLAVOR,
              image_selector=settings.OPENSTACK_SANDBOX_BASE_IMAGE,
              key_name=settings.OPENSTACK_SANDBOX_SSH_KEYNAME,
              **kwargs):
        """
        Get a server instance started and an openstack_id assigned

        TODO: Add handling of quota limitations & waiting list
        TODO: Create the key dynamically
        """
        self.logger.info('Starting server (status=%s)...', self.status)
        self._status_to_building()
        try:
            os_server = openstack_utils.create_server(
                self.nova,
                self.name,
                flavor_selector=flavor_selector,
                image_selector=image_selector,
                key_name=key_name,
                **kwargs
            )
        except novaclient.exceptions.ClientException as exc:
            self.logger.error('Failed to start server: %s', exc)
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
        Stop and terminate the server.

        We explicitly stop and wait for a graceful shutdown of the server before terminating it.
        This ensures any daemons that need to perform cleanup tasks can do so, or that any
        shutdown scripts/tasks get executed.
        """
        # We should delete SSH key before terminating a server.
        # Edge cases: server is still being configured or has incorrect status due to an error.
        self._delete_ssh_key()

        if self.status == Status.Terminated:
            return

        self.logger.info('Terminating server (status=%s)...', self.status)
        if not self.vm_created:
            self.logger.info('Note: server was not created when terminated.')
            self._status_to_terminated()
            return

        try:
            os_server = self.os_server
            server_closed = self._shutdown(os_server)

            if not server_closed:
                self.logger.warning("Server has not reached SHUTOFF state after max wait time; terminating forcefully.")
            os_server.delete()
        except novaclient.exceptions.NotFound:
            self.logger.error('Error while attempting to terminate server: could not find OS server')
            self._status_to_terminated()
        except (requests.RequestException, novaclient.exceptions.ClientException) as exc:
            self.logger.error('Unable to reach the OpenStack API due to %s', exc)
            if self.status != Status.Unknown:
                self._status_to_unknown()
        else:
            self._status_to_terminated()

    def _shutdown(self, os_server, poll_interval=10, max_wait=None):
        """
        Shutdown the server and wait to return until shutdown or wait threshold reached.

        We don't have an explicit state for this and don't catch exceptions, which is why this is private.
        The caller is expected to handle any exceptions and retry if necessary.
        """
        # We purposely check for `None` rather than generically for falseness
        # because it allows `max_wait = 0`.
        max_wait = max_wait if max_wait is not None else settings.SHUTDOWN_TIMEOUT

        os_server.stop()
        while max_wait > 0 and os_server.status != 'SHUTOFF':
            time.sleep(poll_interval)
            max_wait -= poll_interval
            os_server = self.os_server
        return os_server.status == 'SHUTOFF'

    def _delete_ssh_key(self) -> None:
        """
        Delete SSH key from `~/.ssh/known_hosts`.

        We can safely ignore the command's return code, because we just need to be sure that the key has been removed
        for non-existing server - we don't care about non-existing keys.
        """
        self.logger.info('Deleting SSH key of "%s" host.', self.public_ip)
        command = f'ssh-keygen -R {self.public_ip}'
        try:
            subprocess.Popen(command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.SubprocessError as e:
            self.logger.error('Failed to delete SSH key of "%s" host: %s', self.public_ip, e)
