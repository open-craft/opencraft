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

from instance.models.appserver import Status as AppServerStatus
from instance.models.load_balancer import LoadBalancingServer
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory

# Functions ###################################################################


# pylint: disable=too-many-branches
def make_test_appserver(instance=None, s3=False, server=None, organization=None, status=None):
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

    if server:
        appserver.server = server
        appserver.save()

    if status == AppServerStatus.Running:
        _set_appserver_running(appserver)
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
