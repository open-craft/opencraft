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
from instance.models.appserver import Status as AppServerStatus
from instance.models.server import OpenStackServer, Status as ServerStatus
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
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


@ddt.ddt
class CleanUpTestCase(TestCase):
    """
    Test cases for clean up tasks
    """

    @staticmethod
    def _set_appserver_configuration_failed(appserver):
        """
        Transition `appserver` to Status.ConfigurationFailed.
        """
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_configuration_failed()

    @staticmethod
    def _set_appserver_running(appserver):
        """
        Transition `appserver` to Status.Running.
        """
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_running()

    def _create_appserver(self, instance, created, status):
        """
        Return appserver for `instance` that was `created` on a specific date, and has `status`.

        Note that there is no need to set the status of the VM (OpenStackServer)
        that is associated with the app server to something other than ServerStatus.Pending:

        Servers are allowed to transition to ServerStatus.Terminated from any state,
        and this class does not test functionality for terminating servers itself.
        """
        appserver = make_test_appserver(instance)
        appserver.created = created
        appserver.save()
        if status == AppServerStatus.Running:
            self._set_appserver_running(appserver)
        elif status == AppServerStatus.ConfigurationFailed:
            self._set_appserver_configuration_failed(appserver)
        return appserver

    def _create_running_appserver(self, instance, created):
        """
        Return running app server for `instance` that was `created` on a specific date,
        and has `status` AppServerStatus.Running.
        """
        return self._create_appserver(instance, created, AppServerStatus.Running)

    def _create_failed_appserver(self, instance, created):
        """
        Return running app server for `instance` that was `created` on a specific date,
        and has `status` AppServerStatus.ConfigurationFailed.
        """
        return self._create_appserver(instance, created, AppServerStatus.ConfigurationFailed)

    def _assert_status(self, appservers):
        """
        Assert that status of app servers in `appservers` matches expected status.

        Assumes that `appservers` is an iterable of tuples of the following form:

            (<appserver>, <expected status>, <expected server status>)

        where <expected status> is the expected AppServerStatus of <appserver>,
        and <expected server status> is the expected ServerStatus of the OpenStackServer associated with <appserver>.
        """
        for appserver, expected_status, expected_server_status in appservers:
            appserver.refresh_from_db()
            self.assertEqual(appserver.status, expected_status)
            # Status of appserver.server is still stale after refresh_from_db, so reload server manually:
            server = OpenStackServer.objects.get(id=appserver.server.pk)
            self.assertEqual(server.status, expected_server_status)

    def test_terminate_obsolete_appservers(self):
        """
        Test that `terminate_obsolete_appservers` correctly identifies and terminates app servers
        that were created (more than) two days before the currently-active app server of individual instances.
        """
        instance = OpenEdXInstanceFactory()
        reference_date = timezone.now()

        # Create app servers
        obsolete_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=5))
        obsolete_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=5))

        recent_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=1))
        recent_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=1))

        active_appserver = self._create_running_appserver(instance, reference_date)

        newer_appserver = self._create_running_appserver(instance, reference_date + timedelta(days=3))
        newer_appserver_failed = self._create_failed_appserver(instance, reference_date + timedelta(days=3))

        # Set single app server active
        instance.active_appserver = active_appserver
        instance.save()

        # Run task
        tasks.terminate_obsolete_appservers()

        # Check status of running app servers
        self._assert_status([
            (obsolete_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (recent_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (active_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (newer_appserver, AppServerStatus.Running, ServerStatus.Pending),
        ])

        # Check status of failed app servers:
        # AppServerStatus.Terminated is reserved for instances that were running successfully at some point,
        # so app servers with AppServerStatus.ConfigurationFailed will still have that status
        # after `terminate_obsolete_appservers` calls `terminate_vm` on them.
        # However, the VM (OpenStackServer) that an app server is associated with *should* have ServerStatus.Terminated
        # if the app server was old enough to be terminated.
        self._assert_status([
            (obsolete_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (recent_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (newer_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
        ])

    def test_terminate_obsolete_appservers_no_active(self):
        """
        Test that `terminate_obsolete_appservers` does not terminate any app servers
        if an instance does not have an active app server.
        """
        instance = OpenEdXInstanceFactory()
        reference_date = timezone.now()

        # Create app servers
        obsolete_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=5))
        obsolete_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=5))

        recent_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=1))
        recent_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=1))

        appserver = self._create_running_appserver(instance, reference_date)
        appserver_failed = self._create_failed_appserver(instance, reference_date)

        newer_appserver = self._create_running_appserver(instance, reference_date + timedelta(days=3))
        newer_appserver_failed = self._create_failed_appserver(instance, reference_date + timedelta(days=3))

        # Run task
        tasks.terminate_obsolete_appservers()

        # Check status of app servers (should be unchanged)
        self._assert_status([
            (obsolete_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (obsolete_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (recent_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (recent_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (appserver, AppServerStatus.Running, ServerStatus.Pending),
            (appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (newer_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (newer_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
        ])

    @ddt.data(
        {'pr_state': 'closed', 'pr_days_since_closed': 4, 'instance_shut_down': False},
        {'pr_state': 'closed', 'pr_days_since_closed': 7, 'instance_shut_down': True},
        {'pr_state': 'closed', 'pr_days_since_closed': 10, 'instance_shut_down': True},
        {'pr_state': 'open', 'pr_days_since_closed': None, 'instance_shut_down': False},
    )
    @patch('instance.models.openedx_instance.OpenEdXMonitoringMixin.disable_monitoring')
    def test_shut_down_instances(self, data, mock_disable_monitoring):
        """
        Test that `shut_down_instances` correctly identifies and shuts down instances
        whose PRs got merged (more than) one week ago.
        """
        reference_date = timezone.now()

        # Create PR and instance
        pr = make_watched_pr_and_instance()
        instance = pr.instance

        appserver = self._create_running_appserver(instance, reference_date - timedelta(days=14))
        appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=12))

        newer_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=5))
        newer_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=3))

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
            tasks.shut_down_instances()

            # Check status of app servers
            if data['instance_shut_down']:
                self._assert_status([
                    (appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
                    (appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
                    (newer_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
                    (newer_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
                ])
                self.assertEqual(mock_disable_monitoring.call_count, 1)
            else:
                self._assert_status([
                    (appserver, AppServerStatus.Running, ServerStatus.Pending),
                    (appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
                    (newer_appserver, AppServerStatus.Running, ServerStatus.Pending),
                    (newer_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
                ])
                self.assertEqual(mock_disable_monitoring.call_count, 0)

    @patch('instance.models.openedx_instance.OpenEdXAppServer.terminate_vm')
    @patch('instance.models.openedx_instance.OpenEdXMonitoringMixin.disable_monitoring')
    def test_shut_down_instances_no_pr(self, mock_disable_monitoring, mock_terminate_vm):
        """
        Test that `shut_down_instances` does not shut down instances
        that are not associated with a PR.
        """
        instance = OpenEdXInstanceFactory()
        date = timezone.now()

        self._create_running_appserver(instance, date)

        tasks.shut_down_instances()

        for mocked_method in (mock_disable_monitoring, mock_terminate_vm):
            self.assertEqual(mocked_method.call_count, 0)

    @patch('instance.tasks.terminate_obsolete_appservers')
    @patch('instance.tasks.shut_down_instances')
    def test_clean_up_task(self, mock_shut_down_instances, mock_terminate_obsolete_appservers):
        """
        Test that `clean_up` task spawns `shut_down_instances` and `terminate_obsolete_appservers` tasks.
        """
        tasks.clean_up()
        mock_shut_down_instances.assert_called_once_with()
        mock_terminate_obsolete_appservers.assert_called_once_with()
