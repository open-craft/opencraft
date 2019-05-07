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
Tests - Integration - Base
"""

# Imports #####################################################################
from unittest.mock import patch

from huey.contrib import djhuey

from instance.models.load_balancer import LoadBalancingServer
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.server import OpenStackServer
from instance.tests.base import TestCase


# Tests #######################################################################
class IntegrationTestCase(TestCase):
    """
    Base class for API tests
    """
    def setUp(self):
        super().setUp()
        # Override the environment setting - always run task in the same process
        djhuey.HUEY.always_eager = True
        # Use a reduced playbook for integration builds - it will run faster.
        # See https://github.com/open-craft/configuration/blob/integration/playbooks/opencraft_integration.yml
        patcher = patch(
            'instance.models.openedx_instance.get_base_playbook_name',
            return_value='playbooks/opencraft_integration.yml'
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    def tearDown(self):
        # Trigger clean-up operations for load-balancers and instances.  To avoid reconfiguring the
        # load balancing server multiple time, we first remove the configured load balancer from all
        # instances, then delete the load balancers, then delete the instances.
        for instance in OpenEdXInstance.objects.iterator():
            instance.load_balancing_server = None
            instance.save()
        for load_balancer in LoadBalancingServer.objects.iterator():
            load_balancer.delete()
        for instance in OpenEdXInstance.objects.iterator():
            instance.delete(ignore_errors=True)

        super().tearDown()

        # All VMs should be terminated at this point, but check just in case:
        if OpenStackServer.objects.exclude_terminated().count():
            OpenStackServer.objects.terminate()
            raise AssertionError(
                "Expected all OpenStackServers to be terminated, but some were still running. "
                "(They have now been stopped.)"
            )
