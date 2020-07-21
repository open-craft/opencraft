# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Instance app models - Open EdX Deployment models
"""

from django.contrib.postgres.fields import JSONField
from django.db import models

from instance.models.appserver import Status
from instance.models.deployment import Deployment
from instance.models.openedx_instance import OpenEdXInstance
from instance.utils import DjangoChoiceEnum


# Enums #######################################################################


class DeploymentState(DjangoChoiceEnum):
    """
    The different possible states for a deployment
    """
    # All AppServers in Deployment are healthy
    healthy = 'healthy'
    # Some AppServers in Deployment are offline
    unhealthy = 'unhealthy'
    # All AppServers in Deployment are offline
    offline = 'offline'
    # One or more AppServers in Deployment are being configured
    provisioning = 'provisioning'
    # The instance (and deployment) itself doesn't exist and is being set up
    preparing = 'preparing'
    # Changes have been made but are still pending.
    changes_pending = 'pending'


# Models ######################################################################

class OpenEdXDeployment(Deployment):
    """
    OpenEdXDeployment: A deployment of Open edX and related services.

    Can include multiple AppServers.

    ``changes`` field contains diff between old and new deployment
    configuration in format described here: https://dictdiffer.readthedocs.io/en/latest/#usage
    """

    # TODO: we should write custom validator for this
    changes = JSONField(null=True, blank=True)
    # Field which denotes if the deployment was cancelled by the user
    cancelled = models.BooleanField(default=False)

    def status(self):
        """
        Current state of deployment.

        This returns an aggregate state for the deployment, and will be one of:

        DeploymentState.healthy:
            The desired number of AppServers are active and healthy for this deployment.
        DeploymentState.changes_pending:
            The deployment is new and hasn't started provisioning yet.
        DeploymentState.provisioning:
            The deployment has one or more AppServers provisioning.
        DeploymentState.unhealthy:
            The deployment is not provisioning and doesn't have the required number of
            AppServers running.
        DeploymentState.offline:
            The deployment is not provisioning and has no AppServers running.

        :return: A DeploymentState for the deployment
        """
        appservers_statuses = self.openedxappserver_set.values_list('_status', flat=True)

        # There are no AppServers yet so this deployment is still being set up.
        if not appservers_statuses:
            return DeploymentState.changes_pending

        configuring_states = Status.states_with(ids_only=True, is_configuration_state=True)

        appservers_healthy = 0
        appservers_provisioning = 0
        appservers_unhealthy = 0
        for appservers_status in appservers_statuses:
            if appservers_status == Status.Running.state_id:
                appservers_healthy += 1
            elif appservers_status in configuring_states:
                # Provisioning servers are those in the New, WaitingForServer and ConfiguringServer states
                appservers_provisioning += 1
            else:
                # What's left are the ConfigurationFailed, Error, and Terminated states which are unhealthy
                appservers_unhealthy += 1

        instance: OpenEdXInstance = self.instance.instance
        healthy_server_count = instance.openedx_appserver_count

        if appservers_healthy >= healthy_server_count:
            # If the number of running servers is equal or more than required servers
            # consider the deployment healthy even if other servers are being configured/failed
            return DeploymentState.healthy

        # There are some provisioning servers, so overall we are provisioning even if
        # there are some unhealthy servers.
        if appservers_provisioning > 0:
            return DeploymentState.provisioning

        # At this point no AppSevers are provisioning, and there aren't enough healthy servers.
        # There are some healthy AppServers, and some have failed/terminated, so we are
        # overall unhealthy
        if appservers_healthy > 0:
            return DeploymentState.unhealthy

        # At this point no AppServer is healthy or provisioning so we are simply offline
        return DeploymentState.offline

    def get_provisioning_appservers(self):
        """
        Returns a list of AppServers that are currently in the process of being launched.
        """
        in_progress_statuses = Status.states_with(ids_only=True, is_confuguration_state=True)
        return self.openedxappserver_set.filter(_status__in=in_progress_statuses)

    def terminate_deployment(self, force=False):
        """
        Terminate a deployment by terminating all its AppSevers.

        :param force: Force termination even if deployment AppSever is active.
        :return Whether termination was initiated or not
        """
        appservers = self.openedxappserver_set.all()

        # There is an active appserver in this deployment, it shouldn't be cancelled
        if any(appserver.is_active for appserver in appservers) and not force:
            return False

        for appserver in appservers:
            appserver.terminate_vm()

        return True

    def cancel_deployment(self, force=False):
        """
        Mark the deployment as cancelled, and terminate associated appservers"
        """
        self.cancelled = True
        self.save()
        self.terminate_deployment(force)

    @property
    def first_activated(self):
        """
        Returns the activation date for the first activated ``AppServer`` for
        this Deployment, or ``None`` if there is no AppServer, or no AppServer
        has yet been activated.
        :return: Union[None, datetime]
        """
        try:
            first_activated_appserver = self.openedxappserver_set.filter(
                last_activated__isnull=False
            ).earliest('last_activated')
            return first_activated_appserver.last_activated
        except models.ObjectDoesNotExist:
            return None

    class Meta:
        verbose_name = 'Open edX Deployment'
        ordering = ('-created',)
        get_latest_by = 'created'
