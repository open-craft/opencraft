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
OpenEdXInstance monitoring mixins - tests
"""

# Imports #####################################################################

from unittest.mock import call, patch
from uuid import uuid4

from django.test import override_settings

from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

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
        appserver_id = instance.spawn_appserver()  # pylint: disable=no-member
        instance.set_appserver_active(appserver_id)  # pylint: disable=no-member
        self.assertEqual(mock_enable_monitoring.call_count, 1)

    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    def test_delete(self, mock_disable_monitoring):
        """
        Check that monitoring is disabled when an appserver is deleted.
        """
        instance = OpenEdXInstanceFactory()
        instance.delete()  # pylint: disable=no-member
        self.assertEqual(mock_disable_monitoring.call_count, 1)

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_enable_monitoring(self, mock_newrelic):
        """
        Check that the `enable_monitoring` method creates New Relic Synthetics
        monitors for each of the instance's public urls, and enables email
        alerts.
        """
        monitor_ids = [str(uuid4()) for i in range(3)]
        mock_newrelic.get_synthetics_monitors.return_value = []
        mock_newrelic.create_synthetics_monitor.side_effect = monitor_ids
        instance = OpenEdXInstanceFactory()
        instance.enable_monitoring()  # pylint: disable=no-member

        # Check that the monitors have been created
        mock_newrelic.delete_synthetics_monitor.assert_not_called()
        mock_newrelic.create_synthetics_monitor.assert_has_calls([
            call(instance.url),  # pylint: disable=no-member
            call(instance.studio_url),  # pylint: disable=no-member
            call(instance.lms_preview_url),  # pylint: disable=no-member
        ], any_order=True)
        self.assertCountEqual(
            instance.new_relic_availability_monitors.values_list('pk', flat=True),  # pylint: disable=no-member
            monitor_ids
        )

        # Check that alert emails have been set up
        mock_newrelic.add_synthetics_email_alerts.assert_has_calls([
            call(monitor_id, ['admin@opencraft.com'])
            for monitor_id in monitor_ids
        ], any_order=True)

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_update_monitoring(self, mock_newrelic):
        """
        Check that the `enable_monitoring` method only creates New Relic
        Synthetics monitors for urls that are not already monitored, and
        removes monitors for urls that are no longer used.
        """
        instance = OpenEdXInstanceFactory()
        existing_monitors = [
            instance.new_relic_availability_monitors.create(pk=str(uuid4()))  # pylint: disable=no-member
            for i in range(2)
        ]
        mock_newrelic.get_synthetics_monitors.return_value = [
            # This monitor is fine, keep it
            {
                'id': existing_monitors[0].pk,
                'uri': instance.url,  # pylint: disable=no-member
            },
            # This monitor is for an old url, delete it
            {
                'id': existing_monitors[1].pk,
                'uri': 'http://example.com/old-url',
            },
        ]
        new_ids = [str(uuid4()) for i in range(2)]
        mock_newrelic.create_synthetics_monitor.side_effect = new_ids
        instance.enable_monitoring()  # pylint: disable=no-member

        # Check that the old monitor has been deleted and that new monitors
        # have been created
        mock_newrelic.delete_synthetics_monitor.assert_called_once_with(existing_monitors[1].pk)
        mock_newrelic.create_synthetics_monitor.assert_has_calls([
            call(instance.studio_url),  # pylint: disable=no-member
            call(instance.lms_preview_url),  # pylint: disable=no-member
        ], any_order=True)
        self.assertCountEqual(
            instance.new_relic_availability_monitors.values_list('pk', flat=True),  # pylint: disable=no-member
            [existing_monitors[0].pk] + new_ids
        )

    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_disable_monitoring(self, mock_newrelic):  # pylint: disable=no-self-use
        """
        Check that the `disable_monitoring` method removes any New Relic
        Synthetics monitors for this instance.
        """
        monitor_ids = [str(uuid4()) for i in range(3)]
        instance = OpenEdXInstanceFactory()
        for monitor_id in monitor_ids:
            instance.new_relic_availability_monitors.create(pk=monitor_id)  # pylint: disable=no-member
        instance.disable_monitoring()  # pylint: disable=no-member
        mock_newrelic.delete_synthetics_monitor.assert_has_calls([
            call(monitor_id) for monitor_id in monitor_ids
        ], any_order=True)
