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
Load-balanced instance mixin - tests
"""

# Imports #####################################################################

from django.test import override_settings

from instance import gandi
from instance.models.load_balancer import LoadBalancingServer
from instance.models.mixins.load_balanced import LoadBalancedInstance
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_gandi, patch_services


# Tests #######################################################################

class LoadBalancedInstanceTestCase(TestCase):
    """
    Tests for OpenEdXStorageMixin
    """

    def _verify_dns_records(self, instance, domain):
        """
        Verify that DNS records have been set correctly for the given domain.
        """
        lb_domain = instance.load_balancing_server.domain + '.'
        dns_records = gandi.api.client.list_records(domain)
        self.assertCountEqual(dns_records, [
            dict(name='test.dns', type='CNAME', value=lb_domain, ttl=1200),
            dict(name='preview-test.dns', type='CNAME', value=lb_domain, ttl=1200),
            dict(name='studio-test.dns', type='CNAME', value=lb_domain, ttl=1200),
            dict(name='ecommerce-test.dns', type='CNAME', value=lb_domain, ttl=1200),
            dict(name='discovery-test.dns', type='CNAME', value=lb_domain, ttl=1200),
        ])

    @patch_gandi
    def test_set_dns_records(self):
        """
        Test set_dns_records() without external domains.
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.dns.example.com')
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        instance.set_dns_records()
        self._verify_dns_records(instance, 'example.com')

    @patch_gandi
    def test_set_dns_records_external_domain(self):
        """
        Test set_dns_records() with custom external domains.
        Ensure that the DNS records are only created for the internal domains.
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.dns.opencraft.co.uk',
                                          external_lms_domain='courses.myexternal.org',
                                          external_lms_preview_domain='preview.myexternal.org',
                                          external_studio_domain='studio.myexternal.org')
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        instance.set_dns_records()
        self._verify_dns_records(instance, 'opencraft.co.uk')

    @patch_gandi
    def test_remove_dns_records(self):
        """
        Test remove_dns_records().
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.dns.opencraft.co.uk')
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        instance.set_dns_records()
        instance.remove_dns_records()
        dns_records = gandi.api.client.list_records('opencraft.co.uk')
        self.assertEqual(dns_records, [])

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
        appserver = instance.appserver_set.get(pk=appserver_id)
        with self.assertLogs("instance.models.instance") as logs:
            appserver.make_active()
        annotation = instance.get_log_message_annotation()
        for log_line in logs.output:
            self.assertIn(annotation, log_line)
        self.assertEqual(len(logs.output), 3)
        self.assertIn("Triggering reconfiguration of the load balancing server", logs.output[0])
        self.assertIn("New load-balancer configuration", logs.output[1])
        self.assertIn("Setting DNS records for active app servers", logs.output[2])

    @override_settings(PRELIMINARY_PAGE_SERVER_IP=None)
    def test_preliminary_page_not_configured(self):
        """
        Test that get_preliminary_page_config() returns an empty configuration if
        PRELIMINARY_PAGE_SERVER_IP is not set.
        """
        instance = OpenEdXInstanceFactory()
        self.assertEqual(instance.get_preliminary_page_config(instance.ref.pk), ([], []))
