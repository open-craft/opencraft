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
OpenEdXAppServer model - Factories
"""

# Imports #####################################################################
import itertools
from typing import Iterable, Optional

from instance.models.appserver import AppServerState, Status as AppServerStatus
from instance.models.deployment import DeploymentType
from instance.models.load_balancer import LoadBalancingServer
from instance.models.openedx_deployment import OpenEdXDeployment
from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory


# Functions ###################################################################


def make_test_deployment(
        instance: OpenEdXInstance = None,
        active: bool = False,
        appserver_states: Optional[Iterable[AppServerState]] = None,
        deployment_type: DeploymentType = DeploymentType.admin,
) -> OpenEdXDeployment:
    """
    Factory method to create a Deployment for an instance using `make_test_appserver`.

    :param instance: The OpenEdx instance to create an AppServer for, if not
                     given will create a new instance.
    :param appserver_states: states for the AppServers in the deployment
    :param active: Whether the entire set is
    :param deployment_type: Type of deploymetn
    :return: An OpenEdXDeployment instance
    """
    if not instance:
        instance = OpenEdXInstanceFactory()
    if not appserver_states:
        appserver_states = itertools.repeat(AppServerStatus.Running, instance.openedx_appserver_count)
    deployment = OpenEdXDeployment.objects.create(instance=instance.ref, type=deployment_type)

    for appserver_state in appserver_states:
        make_test_appserver(
            instance=instance,
            status=appserver_state,
            is_active=active,
            deployment=deployment,
        )
    return deployment


# pylint: disable=too-many-branches, useless-suppression
def make_test_appserver(  # noqa: MC0001
        instance=None,
        s3=False,
        server=None,
        organization=None,
        status=None,
        is_active=None,
        deployment=None
):
    """
    Factory method to create an OpenEdXAppServer (and OpenStackServer).

    Note that this method does not set the status of the VM (OpenStackServer)
    that is associated with the app server.
    Client code is expected to take care of that itself (if necessary).

    :param instance: The OpenEdx instance to create an AppServer for, if not
                     given will create a new instance.
    :param s3: Will configure S3 storage for the OpenEdXInstance the AppServer
               belongs to.
    :param server: The OpenStackServer to associate with this AppServer.
    :param organization: The organization that owns this AppServer.
    :param status: Will move an AppServer to the specified state
    :param is_active: Will mark the AppServer as active
    :param deployment: Will associate AppServer with the deployment
    :return: appserver for `instance`
    """
    if not instance:
        instance = OpenEdXInstanceFactory()
    if not instance.load_balancing_server:
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
    if s3:
        instance.storage_type = 's3'
        instance.s3_access_key = 'test'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        instance.save()
    if organization:
        instance.ref.owner = organization
        instance.ref.save()
    appserver = instance._create_owned_appserver()

    updated = False

    if server:
        appserver.server = server
        updated = True
    if is_active is not None:
        appserver.is_active = is_active
        updated = True
    if deployment:
        appserver.deployment = deployment
        updated = True
    if updated:
        appserver.save()

    if status == AppServerStatus.Running:
        _set_appserver_running(appserver)
    elif status == AppServerStatus.ConfiguringServer:
        _set_appserver_configuring_server(appserver)
    elif status == AppServerStatus.ConfigurationFailed:
        _set_appserver_configuration_failed(appserver)
    elif status == AppServerStatus.Error:
        _set_appserver_errored(appserver)
    elif status == AppServerStatus.Terminated:
        _set_appserver_terminated(appserver)

    return appserver


def _set_appserver_terminated(appserver):
    """
    Transition `appserver` to AppServerStatus.Terminated.
    """
    appserver._status_to_waiting_for_server()
    appserver._status_to_configuring_server()
    appserver._status_to_running()
    appserver._status_to_terminated()


def _set_appserver_configuring_server(appserver):
    """
    Transition `appserver` to AppServerStatus.Running.
    """
    appserver._status_to_waiting_for_server()
    appserver._status_to_configuring_server()


def _set_appserver_running(appserver):
    """
    Transition `appserver` to AppServerStatus.Running.
    """
    appserver._status_to_waiting_for_server()
    appserver._status_to_configuring_server()
    appserver._status_to_running()


def _set_appserver_configuration_failed(appserver):
    """
    Transition `appserver` to AppServerStatus.ConfigurationFailed.
    """
    appserver._status_to_waiting_for_server()
    appserver._status_to_configuring_server()
    appserver._status_to_configuration_failed()


def _set_appserver_errored(appserver):
    """
    Transition `appserver` to AppServerStatus.Error.
    """
    appserver._status_to_waiting_for_server()
    appserver._status_to_error()
