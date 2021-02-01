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
OpenEdXDeployment model - Tests
"""
from ddt import ddt, unpack, data
from django.test import TestCase

from instance.models.appserver import Status as AppServerStatus
from instance.models.openedx_deployment import DeploymentState
from instance.tests.models.factories.openedx_appserver import make_test_appserver, make_test_deployment
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory

STATUS_SCENARIOS = (
    {
        'server_statuses': [],
        'appserver_count': 1,
        'status': DeploymentState.preparing,
    },
    {
        'server_statuses': [AppServerStatus.ConfiguringServer],
        'appserver_count': 1,
        'status': DeploymentState.preparing,
    },
    {
        'server_statuses': [],
        'appserver_count': 1,
        'status': DeploymentState.changes_pending,
        'additional_deployment': True,
    },
    {
        'server_statuses': [AppServerStatus.ConfiguringServer],
        'appserver_count': 1,
        'status': DeploymentState.provisioning,
        'additional_deployment': True,
    },
    {
        'server_statuses': [AppServerStatus.Running],
        'appserver_count': 1,
        'status': DeploymentState.healthy,
    },
    {
        'server_statuses': [AppServerStatus.Running, AppServerStatus.ConfigurationFailed],
        'appserver_count': 2,
        'status': DeploymentState.unhealthy,
    },
    {
        'server_statuses': [AppServerStatus.Terminated],
        'appserver_count': 1,
        'status': DeploymentState.offline,
    },
)


@ddt
class TestOpenEdXDeployment(TestCase):
    """
    Tests for methods on the OpenEdXDeployment model
    """
    @unpack
    @data(*STATUS_SCENARIOS)
    def test_status(self, server_statuses, appserver_count, status, additional_deployment=False):
        """
        Asserts that the .status() method returns the correct status based on the state of deployments and
        app servers.
        """
        instance = OpenEdXInstanceFactory()
        if additional_deployment:
            deployment = make_test_deployment(instance)
            make_test_appserver(deployment=deployment, instance=instance)
        deployment = make_test_deployment(instance, appserver_states=server_statuses)
        deployment.instance.instance.openedx_appserver_count = appserver_count
        deployment.instance.instance.save()
        self.assertEqual(deployment.status(), status)
