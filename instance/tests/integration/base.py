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
Tests - Integration - Base
"""

# Imports #####################################################################

from huey.contrib import djhuey

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

    def tearDown(self):
        OpenStackServer.objects.terminate()
        super().tearDown()
