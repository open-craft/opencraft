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
from unittest.mock import call, patch, PropertyMock

import ddt
import freezegun
from django.conf import settings
from django.test import override_settings
from django.utils import timezone

from instance import tasks
from instance.models.log_entry import LogEntry
from instance.tests.base import TestCase
from instance.tests.models.factories.load_balancer import LoadBalancingServerFactory
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.server import ReadyOpenStackServerFactory, BootingOpenStackServerFactory
from pr_watch.tests.factories import make_watched_pr_and_instance


# Tests #######################################################################

@ddt.ddt
class SpawnAppServerTestCase(TestCase):
    """
    Test cases for tasks.spawn_appserver, which wraps OpenEdXInstance.spawn_appserver()
    """

    def setUp(self):
        self.spawn_appserver_patcher = patch(
            'instance.models.openedx_instance.OpenEdXInstance.spawn_appserver',
            autospec=True,
        )
        self.addCleanup(self.spawn_appserver_patcher.stop)
        self.mock_spawn_appserver = self.spawn_appserver_patcher.start()
        self.mock_spawn_appserver.return_value = 10

        self.make_appserver_active_patcher = patch('instance.tasks.make_appserver_active')
        self.mock_make_appserver_active = self.make_appserver_active_patcher.start()
        self.addCleanup(self.make_appserver_active_patcher.stop)

    def test_provision_sandbox_instance(self):
        """
        Test the spawn_appserver() task, and that it can be used to spawn an AppServer for a new
        instance.
        """
        instance = OpenEdXInstanceFactory()
        tasks.spawn_appserver(instance.ref.pk)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)
        self.mock_spawn_appserver.assert_called_once_with(
            instance,
            failure_tag=None,
            success_tag=None,
            num_attempts=1
        )
        # By default we don't mark_active_on_success:
        self.assertEqual(self.mock_make_appserver_active.call_count, 0)

    @ddt.data(True, False)
    def test_mark_active_on_success(self, provisioning_succeeds):
        """
        Test that when mark_active_on_success=True, the spawn_appserver task will mark the
        newly provisioned AppServer as active, if provisioning succeeded.
        """
        instance = OpenEdXInstanceFactory()
        server = ReadyOpenStackServerFactory()
        appserver = make_test_appserver(instance=instance, server=server)

        self.mock_spawn_appserver.return_value = appserver.pk if provisioning_succeeds else None
        tasks.spawn_appserver(instance.ref.pk, mark_active_on_success=True)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)
        if provisioning_succeeds:
            self.mock_make_appserver_active.assert_called_once_with(appserver.pk, active=True, deactivate_others=False)
        else:
            self.mock_make_appserver_active.assert_not_called()

    def test_not_mark_active_if_pending(self):
        """
        Test that we when mark_active_on_success=True, the spawn_appserver task will not mark the
        newly provisioned AppServer as active if the OpenStack server is not ready.
        """
        instance = OpenEdXInstanceFactory()
        appserver = make_test_appserver(instance=instance)
        appserver.server = BootingOpenStackServerFactory()
        appserver.save()

        self.mock_spawn_appserver.return_value = appserver.pk
        self.make_appserver_active_patcher.stop()
        self.addCleanup(self.make_appserver_active_patcher.start)

        tasks.spawn_appserver(instance.ref.pk, mark_active_on_success=True)
        self.assertEqual(appserver.is_active, False)

    @ddt.data(True, False)
    def test_deactivate_old_appservers(self, provisioning_succeeds):
        """
        If `mark_active_on_success` and `deactivate_old_appservers` are both passed in as `True`,
        the spawn appserver task will mark the newly provisioned AppServer as active, and deactivate
        old appservers, if provisioning succeeded.
        """
        instance = OpenEdXInstanceFactory()
        server = ReadyOpenStackServerFactory()
        appserver = make_test_appserver(instance=instance, server=server)

        self.mock_spawn_appserver.return_value = appserver.pk if provisioning_succeeds else None
        tasks.spawn_appserver(instance.ref.pk, mark_active_on_success=True, deactivate_old_appservers=True)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)
        if provisioning_succeeds:
            self.mock_make_appserver_active.assert_called_once_with(appserver.pk, active=True, deactivate_others=True)
        else:
            self.mock_make_appserver_active.assert_not_called()

    @patch('instance.models.openedx_instance.OpenEdXInstance._spawn_appserver')
    def test_num_attempts(self, mock_spawn):
        """
        Test that if num_attempts > 1, the spawn_appserver task will automatically re-try
        provisioning.
        """
        instance = OpenEdXInstanceFactory()

        # Disable mocking of retry-enabled spawn_appserver
        self.spawn_appserver_patcher.stop()
        self.addCleanup(self.spawn_appserver_patcher.start)

        # Mock provisioning failure
        mock_spawn.return_value = None

        tasks.spawn_appserver(instance.ref.pk, num_attempts=3, mark_active_on_success=True)

        # Check mocked functions call count
        self.assertEqual(mock_spawn.call_count, 3)
        self.assertEqual(self.mock_make_appserver_active.call_count, 0)

        # Confirm logs
        self.assertTrue(any("Spawning new AppServer, attempt 1 of 3" in log.text for log in instance.log_entries))
        self.assertTrue(any("Spawning new AppServer, attempt 2 of 3" in log.text for log in instance.log_entries))
        self.assertTrue(any("Spawning new AppServer, attempt 3 of 3" in log.text for log in instance.log_entries))

    @patch('instance.models.openedx_instance.OpenEdXInstance._spawn_appserver')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision')
    def test_num_attempts_successful(self, mock_provision, mock_spawn):
        """
        Test that if num_attempts > 1, the spawn_appserver task will stop trying to provision
        after a successful attempt.
        """
        instance = OpenEdXInstanceFactory()

        # Disable mocking of retry-enabled spawn_appserver
        self.spawn_appserver_patcher.stop()
        self.addCleanup(self.spawn_appserver_patcher.start)

        # Mock successful provisioning
        mock_provision.return_value = True
        mock_spawn.return_value = make_test_appserver(instance)

        tasks.spawn_appserver(instance.ref.pk, num_attempts=3, mark_active_on_success=True)

        # Check mocked functions call count
        self.assertEqual(mock_spawn.call_count, 1)
        self.assertEqual(mock_provision.call_count, 1)
        self.assertEqual(self.mock_make_appserver_active.call_count, 1)

        # Confirm logs
        self.assertTrue(any("Spawning new AppServer, attempt 1 of 3" in log.text for log in instance.log_entries))
        self.assertFalse(any("Spawning new AppServer, attempt 2 of 3" in log.text for log in instance.log_entries))
        self.assertFalse(any("Spawning new AppServer, attempt 3 of 3" in log.text for log in instance.log_entries))

    @patch('instance.models.openedx_instance.OpenEdXInstance._spawn_appserver')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision')
    def test_one_attempt_default(self, mock_provision, mock_spawn):
        """
        Test that by default, the spawn_appserver task will not re-try provisioning.
        """
        instance = OpenEdXInstanceFactory()

        # Disable mocking of retry-enabled spawn_appserver
        self.spawn_appserver_patcher.stop()
        self.addCleanup(self.spawn_appserver_patcher.start)

        # Mock successful provisioning
        mock_provision.return_value = True
        mock_spawn.return_value = make_test_appserver(instance)

        tasks.spawn_appserver(instance.ref.pk)

        # Check mocked functions call count
        self.assertEqual(mock_spawn.call_count, 1)
        self.assertEqual(mock_provision.call_count, 1)

        # Confirm logs
        self.assertTrue(any("Spawning new AppServer, attempt 1 of 1" in log.text for log in instance.log_entries))

    @patch('instance.models.openedx_instance.OpenEdXInstance._spawn_appserver')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision')
    def test_one_attempt_default_fail(self, mock_provision, mock_spawn):
        """
        Test that by default, the spawn_appserver task will not re-try provisioning, even when failing.
        """
        instance = OpenEdXInstanceFactory()

        # Disable mocking of retry-enabled spawn_appserver
        self.spawn_appserver_patcher.stop()
        self.addCleanup(self.spawn_appserver_patcher.start)

        # Mock successful provisioning
        mock_provision.return_value = False
        mock_spawn.return_value = make_test_appserver(instance)

        tasks.spawn_appserver(instance.ref.pk)

        # Check mocked functions call count
        self.assertEqual(mock_spawn.call_count, 1)
        self.assertEqual(mock_provision.call_count, 1)

        # Confirm logs
        self.assertTrue(any("Spawning new AppServer, attempt 1 of 1" in log.text for log in instance.log_entries))


@ddt.ddt
class MakeAppserverActiveTestCase(TestCase):
    """
    Test cases for the task that makes an appserver active.
    """

    def setUp(self):
        self.appserver = make_test_appserver()
        self.appserver.server = ReadyOpenStackServerFactory()
        self.appserver.is_active = True
        self.appserver.save()

    @ddt.data(True, False)
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.make_active')
    def test_make_appserver_active(self, active, mock_make_active):
        """
        By default, we activate the appserver.
        """
        tasks.make_appserver_active(self.appserver.id, active=active)
        mock_make_active.assert_called_once_with(active=active)

    @ddt.data([False, True], [False, False])
    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.make_active')
    def test_make_appserver_active_server_unhealthy(self, health, mock_make_active, mock_update_status):
        """
        Test to activate the appserver where the associated server was unhealthy.
        The server is checked for being healthy twice. If it was unhealthy
        for both the calls, the appserver is not made active.
        """
        with patch('instance.models.server.OpenStackServer.Status.Ready.is_healthy_state',
                   new_callable=PropertyMock) as mock_is_healthy_state:
            mock_is_healthy_state.side_effect = health
            tasks.make_appserver_active(self.appserver.id, active=True)
            mock_update_status.assert_called_once_with()
            if any(healthy for healthy in health):
                mock_make_active.assert_called_once_with(active=True)
            else:
                mock_make_active.assert_not_called()

    @patch('instance.models.openedx_appserver.OpenEdXAppServer.make_active')
    def test_deactivate_others(self, mock_make_active):
        """
        When activating the appserver, optionally deactivate others.
        """
        for dummy in range(5):
            appserver = make_test_appserver(self.appserver.instance)
            appserver.is_active = True
            appserver.save()
        tasks.make_appserver_active(self.appserver.id, active=True, deactivate_others=True)
        mock_make_active.assert_has_calls(
            # Calls to make the appserver active.
            [call(active=True)] +
            # Calls to deactivate other appservers.
            [call(active=False) for dummy in range(5)]
        )

    @patch('instance.models.openedx_appserver.OpenEdXAppServer.make_active')
    def test_disallow_deactivating_all(self, mock_make_active):
        """
        Disallow attempts to deactivate all appservers by passing in `active=False` and `deactivate_others=True`.
        """
        # Make an extra appserver to make sure it is not deactivated.
        appserver = make_test_appserver(self.appserver.instance)
        appserver.is_active = True
        appserver.save()
        tasks.make_appserver_active(self.appserver.id, active=False, deactivate_others=True)
        mock_make_active.assert_called_once_with(active=False)


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
        for i in range(5):
            make_watched_pr_and_instance(source_fork_name='some/fork{}'.format(i))

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
            instance = OpenEdXInstanceFactory()
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


class ReconfigureDirtyLoadBalancersTestCase(TestCase):
    """
    Test cases for periodic task that reconfigures all dirty load balancers.
    """

    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    def test_reconfigure_dirty_load_balancers(self, mock_reconfigure):
        """
        `reconfigure_dirty_load_balancers` calls `reconfigure` on all dirty load balancers, and no others.
        """
        # Dirty load balancers.
        for dummy in range(3):
            LoadBalancingServerFactory(configuration_version=10, deployed_configuration_version=1)

        # This is impossible.
        LoadBalancingServerFactory(configuration_version=1, deployed_configuration_version=10)
        # Clean load balancer.
        LoadBalancingServerFactory(configuration_version=2, deployed_configuration_version=2)

        tasks.reconfigure_dirty_load_balancers()
        self.assertEqual(mock_reconfigure.call_count, 3)


class DeleteOldLogsTestCase(TestCase):
    """
    Test cases for periodic task that deletes old logs.
    """

    def setUp(self):
        super().setUp()
        self.now = timezone.datetime(2018, 8, 1, 7, 20, 12)
        self.before_cutoff = self.now - timezone.timedelta(days=settings.LOG_DELETION_DAYS + 1)
        self.log_deletion = self.now + timezone.timedelta(days=1)

        # Some Django start-up tasks produce logs which interfere with our tests.
        LogEntry.objects.all().delete()

    @override_settings(LOG_DELETION_DAYS=30)
    def test_delete_old_logs(self):
        """
        Only logs created before a cutoff date are deleted.
        """
        with freezegun.freeze_time(self.before_cutoff):
            instance = OpenEdXInstanceFactory()
            for i in range(1, 4):
                instance.logger.info('old log {}'.format(i))
        with freezegun.freeze_time(self.now):
            instance.logger.info('new log')
        with freezegun.freeze_time(self.log_deletion):
            total_logs = LogEntry.objects.count()
            total_logs_deleted = LogEntry.objects.filter(created__lte=self.before_cutoff).count()
            tasks.delete_old_logs()

        remaining_logs = LogEntry.objects.order_by('created')
        # 1 extra log was generated to write the deletion query.
        self.assertEqual(remaining_logs.count(), total_logs - total_logs_deleted + 1)
        # The last created log is indeed the deletion query.
        self.assertEqual(
            remaining_logs.last().text,
            "instance.tasks            "
            "| DELETE FROM instance_logentry WHERE instance_logentry.created < '2018-07-03T07:20:12+00:00'::timestamptz"
        )
        # Only the new log remains.
        self.assertFalse(remaining_logs.filter(text__contains='old log').exists())
        self.assertTrue(remaining_logs.filter(text__contains='new log').exists())
