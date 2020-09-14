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
OpenEdXInstance monitoring mixins - tests
"""

# Imports #####################################################################

from unittest.mock import call, patch
from uuid import uuid4

import ddt
import requests
import responses
from django.db.models import ProtectedError
from django.test import override_settings

from instance import newrelic
from instance.models.mixins.openedx_monitoring import (
    NewRelicAvailabilityMonitor,
    NewRelicAlertCondition,
    NewRelicAlertPolicy,
    NewRelicEmailNotificationChannel,
)
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

@ddt.ddt
@override_settings(ADMINS=[('OpenCraft Admin', 'admin@opencraft.com')],
                   NEWRELIC_ADMIN_USER_API_KEY='admin-api-key')
@patch(
    'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class OpenEdXMonitoringTestCase(TestCase):
    """
    Tests for OpenEdXMonitoringMixin.
    """
    @patch_services
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.enable_monitoring')
    def test_set_appserver_active(self, mocks, mock_consul, mock_enable_monitoring):
        """
        Check that monitoring is enabled when an appserver is activated.
        """
        instance = OpenEdXInstanceFactory()
        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        appserver.make_active()
        self.assertEqual(mock_enable_monitoring.call_count, 1)

    @ddt.data(
        # [additional_monitoring_emails, expected final email monitor list]
        [[], ['admin@opencraft.com']],
        [['other@opencraft.com'], ['admin@opencraft.com', 'other@opencraft.com']],
    )
    @ddt.unpack
    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_enable_monitoring(self, additional_monitoring_emails, expected_monitor_emails, mock_newrelic, mock_consul):
        """
        Check that the `enable_monitoring` method creates New Relic Synthetics
        monitors for each of the instance's public urls, and enables email
        alerts.
        """
        monitor_ids = [str(uuid4()) for i in range(4)]
        mock_newrelic.get_synthetics_monitor.return_value = []
        mock_newrelic.get_synthetics_notification_emails.return_value = []
        mock_newrelic.create_synthetics_monitor.side_effect = monitor_ids
        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.add_alert_nrql_condition.side_effect = list(range(4))
        mock_newrelic.add_email_notification_channel.side_effect = list(range(len(expected_monitor_emails)))
        instance = OpenEdXInstanceFactory()
        instance.additional_monitoring_emails = additional_monitoring_emails
        instance.enable_monitoring()

        # Check that the monitors have been created
        mock_newrelic.delete_synthetics_monitor.assert_not_called()
        mock_newrelic.create_synthetics_monitor.assert_has_calls([
            call(instance.url),
            call(instance.studio_url),
            call(instance.lms_preview_url),
            call(instance.lms_extended_heartbeat_url),
        ], any_order=True)
        self.assertCountEqual(
            instance.new_relic_availability_monitors.values_list('pk', flat=True),
            monitor_ids
        )

        # Check that alert emails have been set up
        created_conditions = set()
        list_of_emails_added = []

        for add_call in mock_newrelic.add_alert_nrql_condition.call_args_list:
            created_conditions.add((add_call[0][1], add_call[0][2]))

        for add_call in mock_newrelic.add_email_notification_channel.call_args_list:
            list_of_emails_added.append(add_call[0][0])

        self.assertEqual(
            created_conditions,
            set([
                (instance.url, 'LMS of {}'.format(instance.name)),
                (instance.studio_url, 'Studio of {}'.format(instance.name)),
                (instance.lms_preview_url, 'Preview of {}'.format(instance.name)),
                (instance.lms_extended_heartbeat_url, 'Extended heartbeat of {}'.format(instance.name)),
            ])
        )
        self.assertEqual(set(list_of_emails_added), set(expected_monitor_emails))
        mock_newrelic.add_notification_channels_to_policy.assert_called_with(
            1, list(range(len(expected_monitor_emails)))
        )

    @ddt.data(
        # [additional_monitoring_emails, expected final email monitor list]
        [[], ['admin@opencraft.com']],
        [['other@opencraft.com'], ['admin@opencraft.com', 'other@opencraft.com']],
    )
    @ddt.unpack
    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_long_monitoring_condition_names(self, additional_emails, expected_emails, mock_newrelic, mock_consul):
        """
        Check that the `enable_monitoring` method creates New Relic Synthetics
        monitors for each of the instance's public urls, and enables email
        alerts even for those instance names which has extremely long names.
        """
        monitor_ids = [str(uuid4()) for i in range(4)]
        mock_newrelic.get_synthetics_monitor.return_value = []
        mock_newrelic.get_synthetics_notification_emails.return_value = []
        mock_newrelic.create_synthetics_monitor.side_effect = monitor_ids
        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.add_alert_nrql_condition.side_effect = list(range(4))
        mock_newrelic.add_email_notification_channel.side_effect = list(range(len(expected_emails)))
        instance = OpenEdXInstanceFactory()
        instance.name += " long" * 15  # Generate a very long instance name
        instance.additional_monitoring_emails = additional_emails
        instance.enable_monitoring()

        # Check that the monitors have been created
        mock_newrelic.delete_synthetics_monitor.assert_not_called()
        mock_newrelic.create_synthetics_monitor.assert_has_calls([
            call(instance.url),
            call(instance.studio_url),
            call(instance.lms_preview_url),
            call(instance.lms_extended_heartbeat_url),
        ], any_order=True)
        self.assertCountEqual(
            instance.new_relic_availability_monitors.values_list('pk', flat=True),
            monitor_ids
        )

        # Check that alert emails have been set up
        created_condition_urls = set()
        created_condition_names = set()
        list_of_emails_added = []

        for add_call in mock_newrelic.add_alert_nrql_condition.call_args_list:
            created_condition_urls.add(add_call[0][1])
            created_condition_names.add(add_call[0][2])

        for add_call in mock_newrelic.add_email_notification_channel.call_args_list:
            list_of_emails_added.append(add_call[0][0])

        for condition_name in created_condition_names:
            self.assertTrue(condition_name.endswith("..."))
            self.assertLessEqual(len(condition_name), 64)

        self.assertEqual(created_condition_urls, set([
            instance.url,
            instance.studio_url,
            instance.lms_preview_url,
            instance.lms_extended_heartbeat_url,
        ]))
        self.assertEqual(set(list_of_emails_added), set(expected_emails))
        mock_newrelic.add_notification_channels_to_policy.assert_called_with(1, list(range(len(expected_emails))))

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_enable_monitoring_for_pre_new_relic_alerts_instances(self, mock_newrelic, mock_consul):
        """
        Check that the monitoring is enabled properly for the instances with monitoring
        enabled using the pre-New Relic alerts code.
        """
        instance = OpenEdXInstanceFactory()
        monitor_ids = [str(uuid4()) for i in range(len(instance._urls_to_monitor))]
        for monitor_id in monitor_ids:
            NewRelicAvailabilityMonitor.objects.create(instance=instance, pk=monitor_id)

        existing_monitors = NewRelicAvailabilityMonitor.objects.filter(instance=instance)

        self.assertEqual(existing_monitors.count(), len(instance._urls_to_monitor))
        self.assertEqual(NewRelicAlertPolicy.objects.filter(instance=instance).count(), 0)
        mock_newrelic.get_synthetics_monitor.side_effect = [{'uri': url} for url in instance._urls_to_monitor]
        mock_newrelic.get_synthetics_notification_emails.return_value = ['admin@opencraft.com']
        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.add_alert_nrql_condition.side_effect = list(range(4))
        mock_newrelic.add_email_notification_channel.return_value = 1
        instance.enable_monitoring()
        self.assertEqual(set(NewRelicAvailabilityMonitor.objects.filter(instance=instance)), set(existing_monitors))
        self.assertEqual(NewRelicAlertPolicy.objects.filter(instance=instance).count(), 1)
        self.assertEqual(
            NewRelicEmailNotificationChannel.objects.get(new_relic_alert_policies__id=1).email,
            'admin@opencraft.com'
        )
        self.assertEqual(
            NewRelicAlertCondition.objects.filter(alert_policy__id=1, monitor__id__in=monitor_ids).count(), 4
        )

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_enable_monitoring_does_not_skip_alerts_on_retry_after_error(self, mock_newrelic, mock_consul):
        """
        Check that the enable_monitoring doesn't skip the creation of monitoring resources (New Relic alerts)
        when a previous attempt to enable monitoring failed with an error.
        """
        instance = OpenEdXInstanceFactory()

        class CustomException(Exception):
            """
            Exception to be thrown by mocked code.
            """

        def check(instance):
            """
            Do a first call to enable monitoring, then check that successive calls stop at a certain step
            (not before).
            """
            try:
                instance.enable_monitoring()
            except Exception:  # pylint: disable=broad-except
                pass
            for _ in range(10):
                with self.assertRaises(CustomException):
                    instance.enable_monitoring()

        mock_newrelic.add_alert_policy.side_effect = CustomException()
        check(instance)

        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.get_synthetics_monitor.side_effect = [{'uri': url} for url in instance._urls_to_monitor]
        mock_newrelic.add_alert_nrql_condition.side_effect = CustomException()
        check(instance)

        mock_newrelic.add_alert_nrql_condition.side_effect = list(range(len(instance._urls_to_monitor)))
        mock_newrelic.add_email_notification_channel.side_effect = CustomException()
        check(instance)

        mock_newrelic.add_email_notification_channel.return_value = 1
        mock_newrelic.add_notification_channels_to_policy.side_effect = CustomException()
        check(instance)

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_update_monitoring(self, mock_newrelic, mock_consul):
        """
        Check that the `enable_monitoring` method only creates New Relic
        Synthetics monitors for urls that are not already monitored, and
        removes monitors for urls that are no longer used.
        """
        instance = OpenEdXInstanceFactory()
        existing_monitors = [
            instance.new_relic_availability_monitors.create(pk=str(uuid4()))
            for i in range(2)
        ]

        def mock_get_synthetics_monitor(monitor_id):
            """ Mock for get_synthetics_monitor() """
            if monitor_id == existing_monitors[0].pk:
                # This monitor is fine, keep it
                return {
                    'id': existing_monitors[0].pk,
                    'uri': instance.url,
                }
            elif monitor_id == existing_monitors[1].pk:
                # This monitor is for an old url, delete it
                return {
                    'id': existing_monitors[1].pk,
                    'uri': 'http://example.com/old-url',
                }
            else:
                raise Exception("404")

        mock_newrelic.get_synthetics_monitor.side_effect = mock_get_synthetics_monitor
        new_ids = [str(uuid4()) for i in range(3)]
        mock_newrelic.create_synthetics_monitor.side_effect = new_ids
        other_ids = list(range(4))
        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.add_alert_nrql_condition.side_effect = other_ids
        mock_newrelic.add_email_notification_channel.side_effect = other_ids

        instance.enable_monitoring()

        # Check that the old monitor has been deleted and that new monitors
        # have been created
        mock_newrelic.delete_synthetics_monitor.assert_called_once_with(existing_monitors[1].pk)
        mock_newrelic.create_synthetics_monitor.assert_has_calls([
            call(instance.studio_url),
            call(instance.lms_preview_url),
        ], any_order=True)
        self.assertCountEqual(
            instance.new_relic_availability_monitors.values_list('pk', flat=True),
            [existing_monitors[0].pk] + new_ids
        )

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_update_monitoring_additional_email(self, mock_newrelic, mock_consul):
        """
        Check that the `enable_monitoring` method will add new
        'additional_monitoring_emails' to the existing monitors.
        """
        instance = OpenEdXInstanceFactory()
        existing_monitor_ids = [str(uuid4()) for i in range(4)]
        existing_monitors = {}
        existing_monitor_urls = [
            instance.url,
            instance.studio_url,
            instance.lms_preview_url,
            instance.lms_extended_heartbeat_url
        ]
        for i in range(4):
            new_id = existing_monitor_ids[i]
            instance.new_relic_availability_monitors.create(pk=new_id)
            existing_monitors[new_id] = {'id': new_id, 'uri': existing_monitor_urls[i]}

        def mock_get_synthetics_monitor(monitor_id):
            """ Mock for get_synthetics_monitor() """
            return existing_monitors[monitor_id]

        ssl_monitor_ids = [str(uuid4()) for i in range(4)]
        mock_newrelic.create_synthetics_ssl_monitor.side_effect = ssl_monitor_ids
        mock_newrelic.get_synthetics_monitor.side_effect = mock_get_synthetics_monitor
        mock_newrelic.get_synthetics_notification_emails.return_value = ['admin@opencraft.com']
        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.add_alert_nrql_condition.side_effect = list(range(8))
        mock_newrelic.add_email_notification_channel.return_value = 1
        instance.new_relic_alert_policy = NewRelicAlertPolicy.objects.create(id=1, instance=instance)
        instance.new_relic_alert_policy.email_notification_channels.add(
            NewRelicEmailNotificationChannel.objects.create(id=0, email='admin@opencraft.com')
        )
        NewRelicEmailNotificationChannel.objects.create(id=10, email='existing@opencraft.com')
        instance.additional_monitoring_emails = ['extra@opencraft.com', 'existing@opencraft.com']
        instance.enable_monitoring()

        # Check that the extra email has been added to existing monitors,
        # which should be unchanged
        mock_newrelic.create_synthetics_monitor.assert_not_called()
        mock_newrelic.delete_synthetics_monitor.assert_not_called()
        mock_newrelic.add_email_notification_channel.assert_called_with('extra@opencraft.com')
        mock_newrelic.add_notification_channels_to_policy.assert_called_with(1, [1, 10])

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_disable_monitoring(self, mock_newrelic, mock_consul):
        """
        Check that the `disable_monitoring` method removes any New Relic
        Synthetics monitors for this instance and the alert policy created for the instance
        """
        monitor_ids = [str(uuid4()) for i in range(4)]
        instance = OpenEdXInstanceFactory()
        mock_newrelic.get_synthetics_notification_emails.return_value = []
        mock_newrelic.create_synthetics_monitor.side_effect = monitor_ids
        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.add_alert_nrql_condition.side_effect = list(range(4))
        mock_newrelic.add_email_notification_channel.return_value = 1

        instance.enable_monitoring()
        instance.disable_monitoring()
        mock_newrelic.delete_synthetics_monitor.assert_has_calls([
            call(monitor_id) for monitor_id in monitor_ids
        ], any_order=True)
        mock_newrelic.delete_alert_policy.assert_called_with(1)
        with self.assertRaises(NewRelicAlertPolicy.DoesNotExist):
            NewRelicAlertPolicy.objects.get(instance=instance)

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_email_address_deletion_on_disabling_monitoring(self, mock_newrelic, mock_consul):
        """
        Check that the `disable_monitoring` method removes all the notification email addresses for an instance
        except the shared email addresses.
        """
        monitor_ids = [str(uuid4()) for i in range(4)]
        instance = OpenEdXInstanceFactory()
        mock_newrelic.get_synthetics_notification_emails.return_value = []
        mock_newrelic.create_synthetics_monitor.side_effect = monitor_ids
        ssl_monitor_ids = [str(uuid4()) for i in range(4)]
        mock_newrelic.create_synthetics_ssl_monitor.side_effect = ssl_monitor_ids
        mock_newrelic.add_alert_policy.return_value = 1
        mock_newrelic.add_alert_nrql_condition.side_effect = list(range(8))
        mock_newrelic.add_email_notification_channel.return_value = 1
        instance.new_relic_alert_policy = NewRelicAlertPolicy.objects.create(id=1, instance=instance)
        instance.new_relic_alert_policy.email_notification_channels.add(
            NewRelicEmailNotificationChannel.objects.create(id=10, email='admin@opencraft.com', shared=True)
        )
        instance.additional_monitoring_emails = ['extra@opencraft.com']
        instance.enable_monitoring()
        self.assertEqual(
            NewRelicEmailNotificationChannel.objects.filter(
                email__in=['admin@opencraft.com', 'extra@opencraft.com']
            ).count(),
            2
        )
        instance.disable_monitoring()
        with self.assertRaises(NewRelicEmailNotificationChannel.DoesNotExist):
            NewRelicEmailNotificationChannel.objects.get(email='extra@opencraft.com')
        NewRelicEmailNotificationChannel.objects.get(email='admin@opencraft.com')

    def test_deleting_shared_notification_email_address(self, mock_consul):
        """
        Test that a shared email notification channel can't be deleted.
        Shared notification channels are used by many instances, so if one instance deleted it, the others
        wouldn't be able to use it.
        """
        e = NewRelicEmailNotificationChannel.objects.create(id=1, email='test@opencraft.com', shared=True)
        with self.assertRaises(ProtectedError):
            e.delete()

    @responses.activate
    def test_disable_monitoring_monitors_not_found(self, mock_consul):
        """
        Test that the `disable_monitoring` method removes any New Relic
        Synthetics monitors for this instance, even if the actual monitors no longer exist.
        """
        monitor_ids = [str(uuid4()) for i in range(3)]
        instance = OpenEdXInstanceFactory()

        for monitor_id in monitor_ids:
            instance.new_relic_availability_monitors.create(pk=monitor_id)
            responses.add(
                responses.DELETE,
                '{0}/monitors/{1}'.format(newrelic.SYNTHETICS_API_URL, monitor_id),
                status=requests.codes.not_found
            )

        # Precondition
        self.assertEqual(instance.new_relic_availability_monitors.count(), 3)

        # Disable monitoring
        instance.disable_monitoring()

        # Instance should no longer have any monitors associated with it
        self.assertEqual(instance.new_relic_availability_monitors.count(), 0)
