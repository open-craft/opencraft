# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <xavier@opencraft.com>
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
Instance app models - App Server
"""

# Imports #####################################################################

import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel

from instance.logging import ModelLoggerAdapter
from .instance import InstanceReference
from .log_entry import LogEntry
from .server import OpenStackServer
from .utils import ModelResourceStateDescriptor, ResourceState, ValidateModelMixin


# Logging #####################################################################

logger = logging.getLogger(__name__)


# States ######################################################################

class AppServerState(ResourceState):
    """
    A [finite state machine] state describing an app server's state.
    """
    # A state is "steady" if we don't expect it to change.
    # This information can be used to:
    # - delay execution of an operation until the target server reaches a steady state
    # - raise an exception when trying to schedule an operation that depends on a state change
    #   while the target server is in a steady state
    # Steady states include:
    # - Status.New
    # - Status.Running
    # - Status.ConfigurationFailed
    # - Status.Error
    # - Status.Terminated
    is_steady_state = True

    # An instance is healthy if it is part of a normal (expected) workflow.
    # This information can be used to detect problems and highlight them in the UI or notify users.
    # Healthy states include:
    # - Status.New
    # - Status.WaitingForServer
    # - Status.ConfiguringServer
    # - Status.Running
    # - Status.Terminated
    is_healthy_state = True


class Status(ResourceState.Enum):
    """
    The states that an AppServer can be in.
    """

    class New(AppServerState):
        """ Newly created """
        state_id = 'new'

    class WaitingForServer(AppServerState):
        """ VM not yet accessible """
        state_id = 'waiting'
        name = 'Waiting for VM'
        is_steady_state = False

    class ConfiguringServer(AppServerState):
        """ Running Ansible playbooks on VM """
        state_id = 'configuring'
        name = 'Configuring VM'
        is_steady_state = False

    class Running(AppServerState):
        """ App server is up and running """
        state_id = 'running'

    class ConfigurationFailed(AppServerState):
        """ App server was not configured successfully (but may be partially online) """
        state_id = 'failed'
        name = 'Configuration failed'
        is_healthy_state = False

    class Error(AppServerState):
        """ App server never got up and running (something went wrong when trying to build new VM) """
        state_id = 'error'
        is_healthy_state = False

    class Terminated(AppServerState):
        """ App server was running successfully and has been shut down """
        state_id = 'terminated'


# Models ######################################################################


class AppServer(ValidateModelMixin, TimeStampedModel):
    """
    AppServer - One or more distinct web applications running on a single VM.

    Owned by an Instance.

    Characteristics of an AppServer:
    * An AppServer object's configuration fields are *immutable*. If you want to change
      configuration, change the Instance's configuration and have it create a new AppServer.
    * An AppServer owns exactly one VM (Server), onto which it installs its applications.
    """
    Status = Status
    status = ModelResourceStateDescriptor(
        state_classes=Status.states, default_state=Status.New, model_field_name='_status'
    )
    _status = models.CharField(
        max_length=20,
        default=status.default_state_class.state_id,
        choices=status.model_field_choices,
        db_index=True,
        db_column='status',
    )
    # State transitions:
    _status_to_waiting_for_server = status.transition(
        from_states=Status.New, to_state=Status.WaitingForServer
    )
    _status_to_configuring_server = status.transition(
        from_states=Status.WaitingForServer, to_state=Status.ConfiguringServer
    )
    _status_to_error = status.transition(
        from_states=Status.WaitingForServer, to_state=Status.Error
    )
    _status_to_running = status.transition(
        from_states=Status.ConfiguringServer, to_state=Status.Running
    )
    _status_to_configuration_failed = status.transition(
        from_states=Status.ConfiguringServer, to_state=Status.ConfigurationFailed
    )
    _status_to_terminated = status.transition(
        from_states=Status.Running, to_state=Status.Terminated
    )

    name = models.CharField(max_length=250, blank=False)
    server = models.OneToOneField(OpenStackServer, on_delete=models.CASCADE, related_name='+')
    # The Instance that owns this. InstanceReference has related_name accessors like 'openedxappserver_set'
    owner = models.ForeignKey(InstanceReference, on_delete=models.CASCADE, related_name='%(class)s_set')
    # When this AppServer was last made the active AppServer of its instance
    last_activated = models.DateTimeField(null=True, blank=True)
    # Used for billing to determine the server running period
    terminated = models.DateTimeField(null=True, blank=True)
    _is_active = models.BooleanField(default=False, db_column="is_active")

    class Meta:
        ordering = ('-created', )
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ModelLoggerAdapter(logger, {'obj': self})

    def __str__(self):
        return self.name

    def get_log_message_annotation(self):
        """
        Format a log line annotation for this AppServer.
        """
        return '{},app_server={} ({!s:.15})'.format(
            self.instance.get_log_message_annotation(), self.pk, self.name
        )

    @property
    def instance(self):
        """
        Get the Instance that owns this AppServer
        """
        return self.owner.instance

    @property
    def event_context(self):
        """
        Context dictionary to include in events
        """
        context = self.instance.event_context  # dict with instance_id
        context.update({'appserver_id': self.pk, 'appserver_type': self.__class__.__name__})
        return context

    @property
    def is_active(self):
        """
        Returns the _is_active value
        """
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        """
        Set the _is_active field.
        Updates last_activated if _is_active was changed, and value = True.
        """
        if bool(self._is_active) != bool(value):
            self._is_active = value
            if self._is_active:
                self.last_activated = timezone.now()

    def save(self, **kwargs):
        if self.pk:
            # We are changing an existing AppServer object. But most AppServer fields are meant
            # to be immutable. Only 'status' and 'modified' are allowed to change.
            if not set(kwargs.get('update_fields', [])) <= set(['_status', 'modified']):
                raise RuntimeError("Error: Attempted to modify an AppServer instance. AppServers are immutable.")
        else:
            # This is a new AppServer. Does it have a Server associated with it yet?
            if not self.server_id:
                self.server = OpenStackServer.objects.create(
                    name_prefix="inst-{}-vm".format(self.owner_id),
                    openstack_region=self.instance.openstack_region,
                )
        super().save(**kwargs)

    def terminate_vm(self):
        """
        Ensure that the VM owned by this instance is terminated.
        """
        self.server.terminate()
        if self.status == Status.Running:
            self._status_to_terminated()
            self.terminated = timezone.now()
            self.save()
        elif self.status == Status.ConfiguringServer:
            self._status_to_configuration_failed()
        elif self.status == Status.WaitingForServer:
            self._status_to_error()

    def _get_log_entries(self, level_list=None, limit=None):
        """
        Return the list of log entry instances for this AppServer and the server it manages,
        optionally filtering by logging level. If a limit is given, only the latest records are
        returned.

        Returns oldest entries first.
        """
        # TODO: Filter out log entries for which the user doesn't have view rights
        appserver_type = ContentType.objects.get_for_model(self)
        server_type = ContentType.objects.get_for_model(self.server)
        entries = LogEntry.objects.filter(
            (Q(content_type=appserver_type) & Q(object_id=self.pk)) |
            (Q(content_type=server_type) & Q(object_id=self.server_id))
        )
        if level_list:
            entries = entries.filter(level__in=level_list)
        if limit:
            # Apply the limit at the SQL/DB level while sorted by descending date, then reverse.
            # Otherwise, we'd have to retrieve all rows and then apply the limit using python.
            return reversed(list(entries[:limit]))
        return entries.order_by('created')

    @property
    def log_entries(self):
        """
        Return the list of log entry instances for this AppServer and the server it manages
        """
        return self._get_log_entries(limit=settings.LOG_LIMIT)

    @property
    def log_error_entries(self):
        """
        Return the list of error or critical log entry instances for this AppServer and the
        server it manages
        """
        return self._get_log_entries(level_list=['ERROR', 'CRITICAL'])
