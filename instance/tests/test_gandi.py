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
Gandi - Tests
"""

# Imports #####################################################################

from unittest.mock import call, patch
import xmlrpc.client

from instance import gandi
from instance.tests.base import TestCase


# Tests #######################################################################

class GandiTestCase(TestCase):
    """
    Test cases for Gandi API calls
    """
    def setUp(self):
        super().setUp()

        with patch('xmlrpc.client.ServerProxy'):
            self.api = gandi.GandiAPI()
            self.api.client.domain.info.return_value = {
                'fqdn': 'test.com',
                'zone_id': 9900,
                # .... full API response contains more fields, but we don't need them in this test.
            }

    def assert_set_dns_record_calls(self, attempts=1):
        """
        Verify Gandi API calls for setting a DNS record value.
        """
        domain_info_call = call.domain.info('TEST_GANDI_API_KEY', 'test.com')
        create_new_zone_version_call = call.domain.zone.version.new('TEST_GANDI_API_KEY', 9900)
        delete_old_record_call = call.domain.zone.record.delete(
            'TEST_GANDI_API_KEY', 9900, 'new_zone_version',
            {'type': ['A', 'CNAME'], 'name': 'sub.domain'}
        )
        create_new_record_call = call.domain.zone.record.add(
            'TEST_GANDI_API_KEY', 9900, 'new_zone_version',
            {'value': '192.168.99.99', 'ttl': 1200, 'type': 'A', 'name': 'sub.domain'}
        )
        set_new_zone_version_call = call.domain.zone.version.set('TEST_GANDI_API_KEY', 9900, 'new_zone_version')

        self.assertEqual(
            self.api.client.mock_calls,
            [domain_info_call] +
            [create_new_zone_version_call] * attempts +
            [delete_old_record_call, create_new_record_call, set_new_zone_version_call]
        )

    def test_get_zone_id(self):
        """
        Gets zone_id for the requested FQDN.
        The zone_id is cached in memory after retreived for the first time.
        """
        zone_id = self.api.get_zone_id('test.com')
        self.assertEqual(zone_id, 9900)
        self.assertEqual(self.api.client.domain.info.call_count, 1)
        zone_id = self.api.get_zone_id('test.com')
        self.assertEqual(zone_id, 9900)
        # Cached zone_id value was used; no additional call to the API was made.
        self.assertEqual(self.api.client.domain.info.call_count, 1)

    def test_set_dns_record(self):
        """
        Set a DNS record value.
        """
        self.api.client.domain.zone.version.new.return_value = 'new_zone_version'
        self.api.set_dns_record('test.com', type='A', name='sub.domain', value='192.168.99.99')
        self.assert_set_dns_record_calls()

    @patch('time.sleep')
    def test_set_dns_record_error_retry_and_succeed(self, sleep):
        """
        Test retry behaviour when setting a DNS record.  Succeed in the third attempt.
        """
        fault = xmlrpc.client.Fault(581091, 'Error')
        self.api.client.domain.zone.version.new.side_effect = [fault, fault, 'new_zone_version']
        self.api.set_dns_record(
            'test.com',
            type='A', name='sub.domain', value='192.168.99.99', attempts=3, retry_delay=3
        )
        self.assert_set_dns_record_calls(attempts=3)
        self.assertEqual(sleep.mock_calls, [call(3), call(6)])

    @patch('time.sleep')
    def test_set_dns_record_error_retry_and_fail(self, sleep):
        """
        Test retry behaviour when setting a DNS record.  Fail all attempts.
        """
        self.api.client.domain.zone.version.new.side_effect = xmlrpc.client.Fault(581091, 'Error')
        with self.assertRaises(xmlrpc.client.Fault):
            self.api.set_dns_record(
                'test.com',
                type='A', name='sub.domain', value='192.168.99.99', attempts=4, retry_delay=2
            )
        self.assertEqual(sleep.mock_calls, [call(2), call(4), call(8)])
