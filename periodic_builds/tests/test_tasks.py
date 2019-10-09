# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2019 OpenCraft <contact@opencraft.com>
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
Periodic builds tasks - Tests
"""

# Imports #####################################################################

from datetime import timedelta
from unittest.mock import patch

from freezegun import freeze_time
from instance.models.appserver import Status as AppServerStatus
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from periodic_builds import tasks

# Tests #######################################################################


class PeriodicBuildsTestCase(TestCase):
    """
    Test cases for tasks.launch_periodic_builds
    """

    @patch("periodic_builds.tasks.spawn_appserver")
    def test_periodic_builds_launched(self, mock_spawn_appserver):
        """
        Test the launch_periodic_builds task
        """

        # set up the instances: two enabled but with different intervals, and
        # one disabled
        instance_enabled = OpenEdXInstanceFactory(
            periodic_builds_interval=timedelta(hours=3),
            periodic_builds_enabled=True,
            periodic_builds_retries=0,
        )
        instance_disabled = OpenEdXInstanceFactory()
        instance_enabled2 = OpenEdXInstanceFactory(
            periodic_builds_interval=timedelta(hours=1),
            periodic_builds_enabled=True,
            periodic_builds_retries=1,
        )
        instance_enabled.save()
        instance_disabled.save()
        instance_enabled2.save()

        with freeze_time("2019-01-03 09:00:00", tz_offset=0):
            tasks.launch_periodic_builds()

            # both enabled instances should have spawned an appserver
            self.assertEqual(mock_spawn_appserver.call_count, 2)
            mock_spawn_appserver.assert_any_call(
                instance_enabled.ref.pk, num_attempts=1, mark_active_on_success=True
            )
            mock_spawn_appserver.assert_any_call(
                instance_enabled2.ref.pk, num_attempts=2, mark_active_on_success=True
            )

            # mock both instances now have appservers
            make_test_appserver(instance_enabled, status=AppServerStatus.Running)
            make_test_appserver(instance_enabled2, status=AppServerStatus.Running)

        mock_spawn_appserver.reset_mock()

        # now we run the task 30 min later
        with freeze_time("2019-01-03 09:30:00", tz_offset=0):
            tasks.launch_periodic_builds()

            # no new appservers should have been spawned (not past any
            # intervals)
            self.assertEqual(mock_spawn_appserver.call_count, 0)

        # now we run the task 2 hours later
        with freeze_time("2019-01-03 11:00:00", tz_offset=0):
            tasks.launch_periodic_builds()

            # the shorter interval instance should have spawned a new one
            mock_spawn_appserver.assert_called_once_with(
                instance_enabled2.ref.pk, num_attempts=2, mark_active_on_success=True
            )
            # fake that we have a new appserver but it's still configuring
            make_test_appserver(instance_enabled2, status=AppServerStatus.ConfiguringServer)

        mock_spawn_appserver.reset_mock()

        # and again in another 3 hours. instance1 is ready, instance2 is ready,
        # but an appserver is still in progress (configuring)
        with freeze_time("2019-01-03 14:00:00", tz_offset=0):
            tasks.launch_periodic_builds()

            mock_spawn_appserver.assert_called_once_with(
                instance_enabled.ref.pk, num_attempts=1, mark_active_on_success=True
            )
