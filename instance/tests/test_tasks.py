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
Worker tasks - Tests
"""

# Imports #####################################################################

from mock import Mock, patch

from instance import tasks
from instance.tests.base import TestCase
from instance.tests.models.factories.instance import OpenEdXInstanceFactory


# Tests #######################################################################

class TasksTestCase(TestCase):
    """
    Test cases for worker tasks
    """
    @patch('instance.tasks.OpenEdXInstance.objects.get_or_create')
    def test_provision_sandbox_instance(self, mock_instance_get_or_create):
        """
        Create sandbox instance
        """
        instance = OpenEdXInstanceFactory()
        mock_instance_get_or_create.return_value = (instance, True)
        instance.run_provisioning = Mock()
        instance.run_provisioning.return_value = ('server', 'log')
        tasks.provision_sandbox_instance(sub_domain='test-provision.sandbox')
        self.assertEqual(instance.run_provisioning.call_count, 1)
