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
Worker tasks - Tests
"""

# Imports #####################################################################

from unittest.mock import patch

import ddt

from instance import tasks
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory


# Tests #######################################################################

# Factory boy doesn't properly support pylint+django
#pylint: disable=no-member

@ddt.ddt
class SpawnAppServerTestCase(TestCase):
    """
    Test cases for tasks.spawn_appserver, which wraps OpenEdXInstance.spawn_appserver()
    """

    def setUp(self):
        patcher = patch('instance.models.openedx_instance.OpenEdXInstance.spawn_appserver', autospec=True)
        self.addCleanup(patcher.stop)
        self.mock_spawn_appserver = patcher.start()
        self.mock_spawn_appserver.return_value = 10

        patcher = patch('instance.models.openedx_instance.OpenEdXInstance.set_appserver_active')
        self.addCleanup(patcher.stop)
        self.mock_set_appserver_active = patcher.start()

    def test_provision_sandbox_instance(self):
        """
        Test the spawn_appserver() task, and that it can be used to spawn an AppServer for a new
        instance.
        """
        instance = OpenEdXInstanceFactory()
        tasks.spawn_appserver(instance.ref.pk)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)
        self.mock_spawn_appserver.assert_called_once_with(instance)
        # By default we don't mark_active_on_success:
        self.assertEqual(self.mock_set_appserver_active.call_count, 0)

    @ddt.data(True, False)
    def test_mark_active_on_success(self, provisioning_succeeds):
        """
        Test that we when mark_active_on_success=True, the spawn_appserver task will mark the
        newly provisioned AppServer as active, if provisioning succeeded.
        """
        self.mock_spawn_appserver.return_value = 10 if provisioning_succeeds else None

        instance = OpenEdXInstanceFactory()
        tasks.spawn_appserver(instance.ref.pk, mark_active_on_success=True)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)

        self.assertEqual(self.mock_set_appserver_active.call_count, 1 if provisioning_succeeds else 0)

    def test_num_attempts(self):
        """
        Test that if num_attempts > 1, the spawn_appserver task will automatically re-try
        provisioning.
        """
        instance = OpenEdXInstanceFactory()

        self.mock_spawn_appserver.return_value = None  # Mock provisioning failure
        tasks.spawn_appserver(instance.ref.pk, num_attempts=3, mark_active_on_success=True)

        self.assertEqual(self.mock_spawn_appserver.call_count, 3)
        self.assertEqual(self.mock_set_appserver_active.call_count, 0)

        self.assertTrue(any("Spawning new AppServer, attempt 1 of 3" in log.text for log in instance.log_entries))
        self.assertTrue(any("Spawning new AppServer, attempt 2 of 3" in log.text for log in instance.log_entries))
        self.assertTrue(any("Spawning new AppServer, attempt 3 of 3" in log.text for log in instance.log_entries))

    def test_one_attempt_default(self):
        """
        Test that by default, the spawn_appserver task will not re-try provisioning.
        """
        instance = OpenEdXInstanceFactory()
        self.mock_spawn_appserver.return_value = None  # Mock provisioning failure
        tasks.spawn_appserver(instance.ref.pk)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)
        self.assertTrue(any("Spawning new AppServer, attempt 1 of 1" in log.text for log in instance.log_entries))
