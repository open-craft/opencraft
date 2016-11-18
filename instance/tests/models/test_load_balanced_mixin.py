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
Load-balanced instance mixin - tests
"""

# Imports #####################################################################

from unittest.mock import patch, call

from django.test import override_settings

from instance.models.load_balancer import LoadBalancingServer
from instance.models.mixins.load_balanced import LoadBalancedInstance
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

class LoadBalancedInstanceTestCase(TestCase):
    """
    Tests for OpenEdXStorageMixin
    """

    @patch('instance.models.mixins.load_balanced.gandi.set_dns_record')
    def test_set_dns_records(self, mock_set_dns_record):
        """
        Test set_dns_records() without external domains.
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.dns.opencraft.com',
                                          use_ephemeral_databases=True)
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        instance.set_dns_records()
        lb_domain = instance.load_balancing_server.domain + "."
        self.assertEqual(mock_set_dns_record.mock_calls, [
            call('opencraft.com', name='test.dns', type='CNAME', value=lb_domain),
            call('opencraft.com', name='preview-test.dns', type='CNAME', value=lb_domain),
            call('opencraft.com', name='studio-test.dns', type='CNAME', value=lb_domain),
        ])

    @patch('instance.models.mixins.load_balanced.gandi.set_dns_record')
    def test_set_dns_records_external_domain(self, mock_set_dns_record):
        """
        Test set_dns_records() with custom external domains.
        Ensure that the DNS records are only created for the internal domains.
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.dns.opencraft.hosting',
                                          external_lms_domain='courses.myexternal.org',
                                          external_lms_preview_domain='preview.myexternal.org',
                                          external_studio_domain='studio.myexternal.org',
                                          use_ephemeral_databases=True)
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        instance.set_dns_records()
        lb_domain = instance.load_balancing_server.domain + "."
        self.assertEqual(mock_set_dns_record.mock_calls, [
            call('opencraft.hosting', name='test.dns', type='CNAME', value=lb_domain),
            call('opencraft.hosting', name='preview-test.dns', type='CNAME', value=lb_domain),
            call('opencraft.hosting', name='studio-test.dns', type='CNAME', value=lb_domain),
        ])

    @patch('instance.models.mixins.load_balanced.gandi.remove_dns_record')
    def test_remove_dns_records(self, mock_remove_dns_record):
        """
        Test remove_dns_records().
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.dns.opencraft.com')
        instance.remove_dns_records()
        self.assertEqual(mock_remove_dns_record.mock_calls, [
            call('opencraft.com', 'test.dns'),
            call('opencraft.com', 'preview-test.dns'),
            call('opencraft.com', 'studio-test.dns'),
        ])

    def test_domains(self):
        """
        Test the get_managed_domains() and get_load_balanced_domains() methods (for test coverage only).
        """
        self.assertEqual(LoadBalancedInstance.get_managed_domains(None), [])
        self.assertEqual(LoadBalancedInstance.get_load_balanced_domains(None), [])

    @patch_services
    def test_reconfigure_load_balancer(self, mock_run_playbook):
        """
        Test that reconfigure_load_balancer reconfigures the load balancer and logs to the instance.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.load_balancer')
        appserver_id = instance.spawn_appserver()
        instance.set_appserver_active(appserver_id)
        with self.assertLogs("instance.models.instance") as logs:
            instance.reconfigure_load_balancer()
        annotation = instance.get_log_message_annotation()
        for log_line in logs.output:
            self.assertIn(annotation, log_line)
        self.assertEqual(len(logs.output), 2)
        self.assertIn("Triggering reconfiguration of the load balancing server", logs.output[0])
        self.assertIn("New load-balancer configuration", logs.output[1])

    @override_settings(PRELIMINARY_PAGE_SERVER_IP=None)
    def test_preliminary_page_not_configured(self):
        """
        Test that get_preliminary_page_config() returns an empty configuration if
        PRELIMINARY_PAGE_SERVER_IP is not set.
        """
        instance = OpenEdXInstanceFactory()
        self.assertEqual(instance.get_preliminary_page_config(instance.ref.pk), ([], []))
