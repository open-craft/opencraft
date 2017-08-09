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

from datetime import timedelta
from unittest.mock import patch

import ddt
from django.utils import timezone

from instance import tasks
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from pr_watch.tests.factories import make_watched_pr_and_instance


# Tests #######################################################################

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

        patcher = patch('instance.tasks.appserver_make_active')
        self.addCleanup(patcher.stop)
        self.mock_add_active_appserver = patcher.start()

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
        self.assertEqual(self.mock_add_active_appserver.call_count, 0)

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

        self.assertEqual(self.mock_add_active_appserver.call_count, 1 if provisioning_succeeds else 0)

    def test_num_attempts(self):
        """
        Test that if num_attempts > 1, the spawn_appserver task will automatically re-try
        provisioning.
        """
        instance = OpenEdXInstanceFactory()

        self.mock_spawn_appserver.return_value = None  # Mock provisioning failure
        tasks.spawn_appserver(instance.ref.pk, num_attempts=3, mark_active_on_success=True)

        self.assertEqual(self.mock_spawn_appserver.call_count, 3)
        self.assertEqual(self.mock_add_active_appserver.call_count, 0)

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


@ddt.ddt
class CleanUpTestCase(TestCase):
    """
    Test cases for clean up tasks
    """

    @staticmethod
    def mock_logger_process(msg, kwargs):
        """
        Mocks the ModelLoggerAdapter.process return value.
        """
        return msg, kwargs

    @patch('instance.logging.ModelLoggerAdapter.process')
    @patch('instance.models.openedx_instance.OpenEdXInstance.terminate_obsolete_appservers')
    def test_terminate_obsolete_appservers(self, mock_terminate_appservers, mock_logger):
        """
        Test that `terminate_obsolete_appservers_all_instances`
        calls `terminate_obsolete_appservers` on all existing instances.
        """
        mock_logger.side_effect = self.mock_logger_process

        for dummy in range(5):
            OpenEdXInstanceFactory()

        tasks.terminate_obsolete_appservers_all_instances()

        self.assertEqual(mock_terminate_appservers.call_count, 5)
        self.assertEqual(mock_logger.call_count, 5)
        mock_logger.assert_called_with("Terminating obsolete appservers for instance", {})

    @ddt.data(
        {'pr_state': 'closed', 'pr_days_since_closed': 4, 'instance_is_archived': False},
        {'pr_state': 'closed', 'pr_days_since_closed': 7, 'instance_is_archived': True},
        {'pr_state': 'closed', 'pr_days_since_closed': 10, 'instance_is_archived': True},
        {'pr_state': 'open', 'pr_days_since_closed': None, 'instance_is_archived': False},
    )
    @patch('instance.logging.ModelLoggerAdapter.process')
    @patch('instance.models.openedx_instance.OpenEdXInstance.archive')
    def test_shut_down_obsolete_pr_sandboxes(self, data, mock_archive, mock_logger):
        """
        Test that `shut_down_obsolete_pr_sandboxes` correctly identifies and shuts down instances
        whose PRs got merged (more than) one week ago.
        """
        mock_logger.side_effect = self.mock_logger_process
        reference_date = timezone.now()

        # Create PRs and instances
        for dummy in range(5):
            make_watched_pr_and_instance()

        # Calculate date when PR was closed
        pr_state = data['pr_state']
        if pr_state == 'closed':
            pr_closed_date = reference_date - timedelta(days=data['pr_days_since_closed'])
            closed_at = pr_closed_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            closed_at = None

        with patch(
            'pr_watch.github.get_pr_info_by_number',
            return_value={'state': pr_state, 'closed_at': closed_at},
        ):
            # Run task
            tasks.shut_down_obsolete_pr_sandboxes()

            # Check if task tried to shut down instances
            if data['instance_is_archived']:
                self.assertEqual(mock_archive.call_count, 5)
                self.assertEqual(mock_logger.call_count, 15)
                mock_logger.assert_called_with("Shutting down obsolete sandbox instance", {})
            else:
                self.assertEqual(mock_archive.call_count, 0)
                self.assertEqual(mock_logger.call_count, 10)

    @patch('instance.models.openedx_instance.OpenEdXInstance.archive')
    def test_shut_down_obsolete_pr_sandboxes_no_pr(self, mock_archive):
        """
        Test that `shut_down_obsolete_pr_sandboxes` does not shut down instances
        that are not associated with a PR.
        """
        for dummy in range(5):
            OpenEdXInstanceFactory()

        tasks.shut_down_obsolete_pr_sandboxes()

        self.assertEqual(mock_archive.call_count, 0)

    @patch('instance.models.openedx_instance.OpenEdXInstance.archive')
    def test_shut_down_obsolete_pr_sandboxes_archived(self, mock_archive):
        """
        Test that `shut_down_obsolete_pr_sandboxes` does not shut down instances
        more than once.
        """
        for dummy in range(5):
            instance = OpenEdXInstanceFactory(i)
            instance.ref.is_archived = True
            instance.save()

        tasks.shut_down_obsolete_pr_sandboxes()

        self.assertEqual(mock_archive.call_count, 0)

    @patch('instance.tasks.terminate_obsolete_appservers_all_instances')
    @patch('instance.tasks.shut_down_obsolete_pr_sandboxes')
    def test_clean_up_task(self, mock_shut_down_sandboxes, mock_terminate_appservers):  # pylint: disable=no-self-use
        """
        Test that `clean_up` task spawns `shut_down_obsolete_pr_sandboxes` and
        `terminate_obsolete_appservers_all_instances` tasks.
        """
        tasks.clean_up()
        mock_shut_down_sandboxes.assert_called_once_with()
        mock_terminate_appservers.assert_called_once_with()
