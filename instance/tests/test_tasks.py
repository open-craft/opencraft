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
Worker tasks - Tests
"""

# Imports #####################################################################


from datetime import timedelta
import logging
from unittest.mock import PropertyMock, call, patch, Mock

import ddt
from django.conf import settings
from django.test import override_settings
from django.utils import timezone
from django.contrib.auth import get_user_model
import freezegun

from instance import tasks
from instance.models.appserver import Status as AppServerStatus
from instance.models.server import Status as ServerStatus
from instance.models.log_entry import LogEntry
from instance.models.openedx_deployment import OpenEdXDeployment
from instance.tasks import make_appserver_active
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver, make_test_deployment
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.server import BootingOpenStackServerFactory, ReadyOpenStackServerFactory
from pr_watch.tests.factories import make_watched_pr_and_instance
from registration.models import BetaTestApplication
from userprofile.models import UserProfile

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

    def call_task_function(self, task_function, instance, **kwargs):
        """
        Call the task functions with appropriate parameters
        """
        if task_function == tasks.start_deployment:  # pylint: disable=comparison-with-callable
            deployment = OpenEdXDeployment.objects.create(instance_id=instance.ref.id).pk
            task_function(instance.ref.pk, deployment, **kwargs)
        else:
            task_function(instance.ref.pk, **kwargs)

    @ddt.data(None, 11)
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_provision_sandbox_instance(self, deployment_id, mock_consul):
        """
        Test the spawn_appserver() task, and that it can be used to spawn an AppServer for a new
        instance.
        """
        instance = OpenEdXInstanceFactory()
        tasks.spawn_appserver(instance.ref.pk, deployment_id=deployment_id)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)
        self.mock_spawn_appserver.assert_called_once_with(
            instance,
            failure_tag=None,
            success_tag=None,
            num_attempts=1,
            deployment_id=deployment_id,
        )
        # By default we don't mark_active_on_success:
        self.assertEqual(self.mock_make_appserver_active.s.call_count, 0)

    @ddt.data(
        (tasks.spawn_appserver, True),
        (tasks.spawn_appserver, False),
        (tasks.start_deployment, True),
        (tasks.start_deployment, False),
    )
    @ddt.unpack
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_mark_active_on_success(self, task_function, provisioning_succeeds, mock_consul):
        """
        Test that when mark_active_on_success=True, the spawn_appserver task will mark the
        newly provisioned AppServer as active, if provisioning succeeded.
        """
        instance = OpenEdXInstanceFactory()
        server = ReadyOpenStackServerFactory()
        appserver = make_test_appserver(instance=instance, server=server)

        self.mock_spawn_appserver.return_value = appserver.pk if provisioning_succeeds else None
        self.call_task_function(task_function, instance, mark_active_on_success=True)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)
        if provisioning_succeeds:
            self.mock_make_appserver_active.s.assert_called_once_with(appserver.pk, active=True)
        else:
            self.mock_make_appserver_active.s.assert_not_called()

    @ddt.data(tasks.spawn_appserver, tasks.start_deployment)
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_not_mark_active_if_pending(self, task_function, mock_consul):
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

        self.call_task_function(task_function, instance, mark_active_on_success=True)
        self.assertEqual(appserver.is_active, False)

    @ddt.data(True, False)
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_deactivate_old_appservers(self, provisioning_succeeds, mock_consul):
        """
        If `mark_active_on_success` and `deactivate_old_appservers` are both passed in as `True`,
        the spawn appserver task will mark the newly provisioned AppServer as active, and deactivate
        old appservers, if provisioning succeeded.
        """
        instance = OpenEdXInstanceFactory()
        server = ReadyOpenStackServerFactory()
        appserver = make_test_appserver(instance=instance, server=server)

        self.mock_spawn_appserver.return_value = appserver.pk if provisioning_succeeds else None
        tasks.spawn_appserver(instance.ref.pk, mark_active_on_success=True)
        self.assertEqual(self.mock_spawn_appserver.call_count, 1)
        if provisioning_succeeds:
            self.mock_make_appserver_active.s.assert_called_once_with(appserver.pk, active=True)
        else:
            self.mock_make_appserver_active.s.assert_not_called()

    @ddt.data(tasks.spawn_appserver, tasks.start_deployment)
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.openedx_instance.OpenEdXInstance._spawn_appserver')
    def test_num_attempts(self, task_function, mock_spawn, mock_consul):
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

        self.call_task_function(task_function, instance, num_attempts=3, mark_active_on_success=True)

        # Check mocked functions call count
        self.assertEqual(mock_spawn.call_count, 3)
        self.assertEqual(self.mock_make_appserver_active.call_count, 0)

        # Confirm logs
        self.assertTrue(any("Spawning new AppServer, attempt 1 of 3" in log.text for log in instance.log_entries))
        self.assertTrue(any("Spawning new AppServer, attempt 2 of 3" in log.text for log in instance.log_entries))
        self.assertTrue(any("Spawning new AppServer, attempt 3 of 3" in log.text for log in instance.log_entries))

    @ddt.data(tasks.spawn_appserver, tasks.start_deployment)
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.openedx_instance.OpenEdXInstance._spawn_appserver')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision')
    def test_num_attempts_successful(self, task_function, mock_provision, mock_spawn, mock_consul):
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

        self.call_task_function(task_function, instance, num_attempts=3, mark_active_on_success=True)

        # Check mocked functions call count
        self.assertEqual(mock_spawn.call_count, 1)
        self.assertEqual(mock_provision.call_count, 1)
        self.assertEqual(self.mock_make_appserver_active.s.call_count, 1)

        # Confirm logs
        self.assertTrue(any("Spawning new AppServer, attempt 1 of 3" in log.text for log in instance.log_entries))
        self.assertFalse(any("Spawning new AppServer, attempt 2 of 3" in log.text for log in instance.log_entries))
        self.assertFalse(any("Spawning new AppServer, attempt 3 of 3" in log.text for log in instance.log_entries))

    @ddt.data(tasks.spawn_appserver, tasks.start_deployment)
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.openedx_instance.OpenEdXInstance._spawn_appserver')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision')
    def test_one_attempt_default(self, task_function, mock_provision, mock_spawn, mock_consul):
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

        self.call_task_function(task_function, instance)

        # Check mocked functions call count
        self.assertEqual(mock_spawn.call_count, 1)
        self.assertEqual(mock_provision.call_count, 1)

        # Confirm logs
        self.assertTrue(any("Spawning new AppServer, attempt 1 of 1" in log.text for log in instance.log_entries))

    @ddt.data(tasks.spawn_appserver, tasks.start_deployment)
    @patch(
        'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.openedx_instance.OpenEdXInstance._spawn_appserver')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision')
    def test_one_attempt_default_fail(self, task_function, mock_provision, mock_spawn, mock_consul):
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

        self.call_task_function(task_function, instance)

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
        with patch(
                'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
                return_value=(1, True)
        ):
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

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.logging.ModelLoggerAdapter.process')
    @patch('instance.models.openedx_instance.OpenEdXInstance.terminate_obsolete_appservers')
    def test_terminate_obsolete_appservers(self, mock_terminate_appservers, mock_logger, mock_consul):
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
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.logging.ModelLoggerAdapter.process')
    @patch('instance.models.openedx_instance.OpenEdXInstance.archive')
    def test_shut_down_obsolete_pr_sandboxes(self, data, mock_archive, mock_logger, mock_consul):
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
                self.assertEqual(mock_logger.call_count, 10)
                mock_logger.assert_called_with("Shutting down obsolete sandbox instance", {})
            else:
                self.assertEqual(mock_archive.call_count, 0)
                self.assertEqual(mock_logger.call_count, 5)

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.openedx_instance.OpenEdXInstance.archive')
    def test_shut_down_obsolete_pr_sandboxes_no_pr(self, mock_archive, mock_consul):
        """
        Test that `shut_down_obsolete_pr_sandboxes` does not shut down instances
        that are not associated with a PR.
        """
        for dummy in range(5):
            OpenEdXInstanceFactory()

        tasks.shut_down_obsolete_pr_sandboxes()

        self.assertEqual(mock_archive.call_count, 0)

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.openedx_instance.OpenEdXInstance.archive')
    def test_shut_down_obsolete_pr_sandboxes_archived(self, mock_archive, mock_consul):
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

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.tasks.terminate_obsolete_appservers_all_instances')
    @patch('instance.tasks.shut_down_obsolete_pr_sandboxes')
    def test_clean_up_task(self, mock_shut_down_sandboxes, mock_terminate_appservers, mock_consul):
        """
        Test that `clean_up` task spawns `shut_down_obsolete_pr_sandboxes` and
        `terminate_obsolete_appservers_all_instances` tasks.
        """
        tasks.clean_up()
        mock_shut_down_sandboxes.assert_called_once_with()
        mock_terminate_appservers.assert_called_once_with()


class DeleteOldLogsTestCase(TestCase):
    """
    Test cases for periodic task that deletes old logs.
    """

    def setUp(self):
        super().setUp()
        self.now = timezone.datetime(2018, 8, 1, 7, 20, 12, tzinfo=timezone.utc)
        self.before_cutoff = self.now - timezone.timedelta(days=settings.LOG_DELETION_DAYS + 1)
        self.log_deletion = self.now + timezone.timedelta(days=1)

        # Some Django start-up tasks produce logs which interfere with our tests.
        LogEntry.objects.all().delete()
        # huey produces logs when running tasks, that interfere with calculations
        logging.getLogger('huey').disabled = True

    @override_settings(LOG_DELETION_DAYS=30)
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_delete_old_logs(self, mock_consul):
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


def gen_appserver_side_effect(deployment, instance, statuses):
    """
    Creates a side-effect function for app-server spawning tests
    so that the tasks can have real database entries to look up
    without invoking any network activity or creating real servers.
    """
    def gen_appserver(*_args, **_kwargs):
        app_server_status, server_status = statuses.pop()
        appserver = make_test_appserver(
            instance=instance,
            status=app_server_status,
            is_active=True,
            deployment=deployment,
        )
        appserver.server._status = server_status
        appserver.server.save()
        return appserver.id
    return gen_appserver


@ddt.ddt
class CreateNewDeploymentTestCase(TestCase):
    """
    Test cases for tasks.start_deployment, which wraps tasks.spawn_appserver.
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

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_new_deployment(self, mock_consul):
        """
        Test the start_deployment() task, and that it can be used to spawn AppServer(s) for a new
        instance.
        """
        instance = OpenEdXInstanceFactory()
        instance.openedx_appserver_count = 3
        instance.save()
        deployment_id = OpenEdXDeployment.objects.create(instance_id=instance.ref.id).pk
        tasks.start_deployment(instance.ref.id, deployment_id).get()
        self.assertEqual(self.mock_spawn_appserver.call_count, 3)
        self.mock_spawn_appserver.assert_has_calls(
            [
                call(
                    instance,
                    failure_tag=None,
                    success_tag=None,
                    num_attempts=1,
                    deployment_id=deployment_id,
                )
                for _ in range(3)
            ]
        )
        # By default we don't mark_active_on_success:
        self.assertEqual(self.mock_make_appserver_active.s.call_count, 0)

    @patch('instance.tasks.OpenEdXAppServer.make_active')
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_multi_appserver_activation(self, mock_consul, mock_make_active):
        """
        Test the start_deployment task, and that it can be used to spawn multiple AppServer(s)
        for a new instance.
        """
        instance = OpenEdXInstanceFactory()
        instance.openedx_appserver_count = 3
        instance.save()
        make_test_deployment(instance, active=True)
        self.mock_make_appserver_active.s = Mock()
        self.mock_make_appserver_active.s.side_effect = make_appserver_active.s
        self.assertEqual(instance.appserver_set.count(), 3)
        appservers = list(instance.appserver_set.all())
        self.assertTrue(all(instance.appserver_set.values_list('_is_active', flat=True)))
        deployment = OpenEdXDeployment.objects.create(instance_id=instance.ref.id)
        statuses = [(AppServerStatus.Running, ServerStatus.Ready.state_id)] * 3
        self.mock_spawn_appserver.side_effect = gen_appserver_side_effect(deployment, instance, statuses)
        with self.assertLogs() as ctx:
            tasks.start_deployment(
                instance.ref.id,
                deployment.pk,
                mark_active_on_success=True,
            ).get()
        self.assertEqual(self.mock_make_appserver_active.s.call_count, 3)
        self.assertEqual(mock_make_active.call_count, 6)
        mock_make_active.assert_has_calls([
            call(active=True),
            call(active=True),
            call(active=True),
            call(active=False),
            call(active=False),
            call(active=False),
        ])
        for appserver in appservers:
            self.assertIn(f'INFO:instance.tasks:Deactivating {appserver} [{appserver.id}]', ctx.output)

    @patch('instance.tasks.OpenEdXAppServer.make_active')
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_multi_appserver_non_activation(self, mock_consul, mock_make_active):
        """
        Test the start_deployment task, and that it can be used to spawn multiple AppServer(s)
        for a new instance.
        """
        instance = OpenEdXInstanceFactory()
        instance.openedx_appserver_count = 3
        instance.save()
        make_test_deployment(instance, active=True)
        self.mock_make_appserver_active.s = Mock()
        self.mock_make_appserver_active.s.side_effect = make_appserver_active.s
        self.assertEqual(instance.appserver_set.count(), 3)
        self.assertTrue(all(instance.appserver_set.values_list('_is_active', flat=True)))
        deployment = OpenEdXDeployment.objects.create(instance_id=instance.ref.id)
        statuses = [(AppServerStatus.Running, ServerStatus.Ready.state_id)] * 3
        self.mock_spawn_appserver.side_effect = gen_appserver_side_effect(deployment, instance, statuses)
        tasks.start_deployment(
            instance.ref.id,
            deployment.pk,
            mark_active_on_success=False,
        ).get()
        self.assertEqual(self.mock_make_appserver_active.s.call_count, 0)
        self.assertEqual(mock_make_active.call_count, 0)

    @patch('instance.tasks.OpenEdXAppServer.make_active')
    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_multi_appserver_partial_activation(self, mock_consul, mock_make_active):
        """
        Test the start_deployment task, and that it can be used to spawn multiple AppServer(s)
        for a new instance.
        """
        instance = OpenEdXInstanceFactory()
        instance.openedx_appserver_count = 3
        instance.save()
        make_test_deployment(instance, active=True)
        self.mock_make_appserver_active.s = Mock()
        self.mock_make_appserver_active.s.side_effect = make_appserver_active.s
        self.assertEqual(instance.appserver_set.count(), 3)
        self.assertTrue(all(instance.appserver_set.values_list('_is_active', flat=True)))
        deployment = OpenEdXDeployment.objects.create(instance_id=instance.ref.id)
        statuses = [
            (AppServerStatus.Running, ServerStatus.Ready.state_id),
            (AppServerStatus.ConfigurationFailed, ServerStatus.BuildFailed.state_id),
            (AppServerStatus.Running, ServerStatus.Ready.state_id),
        ]
        self.mock_spawn_appserver.side_effect = gen_appserver_side_effect(deployment, instance, statuses)
        tasks.start_deployment(
            instance.ref.id,
            deployment.pk,
            mark_active_on_success=False,
        ).get()
        self.assertEqual(self.mock_make_appserver_active.s.call_count, 0)
        self.assertEqual(mock_make_active.call_count, 0)

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_new_deployment_cancelled(self, mock_consul):
        """
        Test the start_deployment() task, and that it can be used to spawn AppServer(s) for a new
        instance.
        """
        instance = OpenEdXInstanceFactory()
        instance.openedx_appserver_count = 1
        instance.save()
        deployment_id = OpenEdXDeployment.objects.create(instance_id=instance.ref.id, cancelled=True).pk
        tasks.start_deployment(instance.ref.id, deployment_id).get()
        self.assertEqual(self.mock_spawn_appserver.call_count, 0)
        self.assertEqual(self.mock_make_appserver_active.s.call_count, 0)


@ddt.ddt
class CleanUpOldBetaTestUserTestCase(TestCase):
    """
    Test cases for tasks.cleanup_old_betatest_users.
    """

    def generate_betatest_user(self, username):
        """
        Helper that creates an user, user profile and beta test
        application instance.
        """

        user = get_user_model().objects.create_user(
            username,
            email='%s@example.com' % username,
            is_active=True
        )
        user_profile = UserProfile.objects.create(
            user=user,
            full_name='test name',
        )
        application = BetaTestApplication.objects.create(
            user=user,
            subdomain=username,
            instance=None,
            instance_name='Test instance',
            project_description='Test instance creation.',
            public_contact_email=user.email,
        )
        return {
            'user': user,
            'profile': user_profile,
            'application': application
        }


    def test_clean_up_betatest_user(self):
        """
        Test if clean up betatest tasks works as expected.
        """

        # generate dataset to test
        data = {
            iden: self.generate_betatest_user(iden)
            for iden in ['user%s' % i for i in range(5)]
        }

        # running task should not delete anything
        tasks.cleanup_old_betatest_users()
        assert BetaTestApplication.objects.all().count() == 5

        inactive_cutoff = timezone.now() - timedelta(
            days=settings.INACTIVE_OLD_BETATEST_USER_DAYS
        )

        # manually change application created date to an old date
        data['user1']['application'].created = inactive_cutoff
        data['user1']['application'].save()

        # user1 should get inactivated and but not deleted.
        tasks.cleanup_old_betatest_users()
        assert not get_user_model().objects.get(username='user1').is_active
        assert BetaTestApplication.objects.all().count() == 5

        # manually change profile modified date to an old date
        delete_cutoff = timezone.now() - timedelta(
            days=settings.DELETE_OLD_BETATEST_USER_DAYS
        )
        with patch('django.utils.timezone.now') as patched_time:
            patched_time.return_value = delete_cutoff
            data['user1']['profile'].modified = delete_cutoff
            data['user1']['profile'].save()

        # user1 should be deleted now
        tasks.cleanup_old_betatest_users()
        assert BetaTestApplication.objects.all().count() == 4
        assert get_user_model().objects.filter(username='user1').count() == 0
