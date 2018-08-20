# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
from django.test import override_settings
import requests
import responses

from instance import newrelic
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

@ddt.ddt
@override_settings(ADMINS=[('OpenCraft Admin', 'admin@opencraft.com')],
                   NEWRELIC_ADMIN_USER_API_KEY='admin-api-key')
class OpenEdXMonitoringTestCase(TestCase):
    """
    Tests for OpenEdXMonitoringMixin.
    """
    @patch_services
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.enable_monitoring')
    def test_set_appserver_active(self, mocks, mock_enable_monitoring):
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
    def test_enable_monitoring(self, additional_monitoring_emails, expected_monitor_emails, mock_newrelic):
        """
        Check that the `enable_monitoring` method creates New Relic Synthetics
        monitors for each of the instance's public urls, and enables email
        alerts.
        """
        monitor_ids = [str(uuid4()) for i in range(4)]
        mock_newrelic.get_synthetics_monitor.return_value = []
        mock_newrelic.get_synthetics_notification_emails.return_value = []
        mock_newrelic.create_synthetics_monitor.side_effect = monitor_ids
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
        created_monitor_ids = set()
        for creation_call in mock_newrelic.add_synthetics_email_alerts.call_args_list:
            created_monitor_ids.add(creation_call[0][0])  # First positional arg to add_synthetics_email_alerts()
            list_of_emails_added = creation_call[0][1]  # Second arg - the list of emails added
            self.assertEqual(set(list_of_emails_added), set(expected_monitor_emails))
        self.assertEqual(set(monitor_ids), created_monitor_ids)

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_update_monitoring(self, mock_newrelic):
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
    def test_update_monitoring_additional_email(self, mock_newrelic):  # pylint: disable=no-self-use
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

        mock_newrelic.get_synthetics_monitor.side_effect = mock_get_synthetics_monitor
        mock_newrelic.get_synthetics_notification_emails.return_value = ['admin@opencraft.com']

        instance.additional_monitoring_emails = ['extra@opencraft.com']
        instance.enable_monitoring()

        # Check that the extra email has been added to existing monitors,
        # which should be unchanged
        mock_newrelic.create_synthetics_monitor.assert_not_called()
        mock_newrelic.delete_synthetics_monitor.assert_not_called()
        mock_newrelic.add_synthetics_email_alerts.assert_has_calls([
            call(existing_monitor_ids[0], ['extra@opencraft.com']),
            call(existing_monitor_ids[1], ['extra@opencraft.com']),
            call(existing_monitor_ids[2], ['extra@opencraft.com']),
        ], any_order=True)

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_disable_monitoring(self, mock_newrelic):  # pylint: disable=no-self-use
        """
        Check that the `disable_monitoring` method removes any New Relic
        Synthetics monitors for this instance.
        """
        monitor_ids = [str(uuid4()) for i in range(3)]
        instance = OpenEdXInstanceFactory()
        for monitor_id in monitor_ids:
            instance.new_relic_availability_monitors.create(pk=monitor_id)
        instance.disable_monitoring()
        mock_newrelic.delete_synthetics_monitor.assert_has_calls([
            call(monitor_id) for monitor_id in monitor_ids
        ], any_order=True)

    @responses.activate
    def test_disable_monitoring_monitors_not_found(self):
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
