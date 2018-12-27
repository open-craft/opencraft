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
Gandi - Tests
"""

# Imports #####################################################################

from unittest.mock import call, patch
import xmlrpc.client

from instance import gandi
from instance.tests.base import TestCase
from instance.tests.fake_gandi_client import FakeGandiClient


# Tests #######################################################################

class GandiTestCase(TestCase):
    """
    Test cases for Gandi API calls
    """
    def setUp(self):
        super().setUp()
        self.api = gandi.GandiAPI(client=FakeGandiClient())

    def populate_cache(self):
        """
        Populate the zone ID cache of the Gandi API and reset the mocks.
        """
        self.api._populate_zone_id_cache()
        self.api.client.domain.reset_mock()

    def assert_set_dns_record_calls(self, attempts=1):
        """
        Verify Gandi API calls for setting a DNS record value.
        """
        create_new_zone_version_call = call.zone.version.new('TEST_GANDI_API_KEY', 9900)
        delete_old_record_call = call.zone.record.delete(
            'TEST_GANDI_API_KEY', 9900, 1,
            {'type': ['A', 'CNAME'], 'name': 'sub.domain'}
        )
        create_new_record_call = call.zone.record.add(
            'TEST_GANDI_API_KEY', 9900, 1,
            {'value': '192.168.99.99', 'ttl': 1200, 'type': 'A', 'name': 'sub.domain'}
        )
        set_new_zone_version_call = call.zone.version.set('TEST_GANDI_API_KEY', 9900, 1)

        self.assertEqual(
            self.api.client.domain.mock_calls,
            [create_new_zone_version_call] * attempts +
            [delete_old_record_call, create_new_record_call, set_new_zone_version_call]
        )

    def test_populate_zone_id_cache(self):
        """
        Test that populating the zone ID cache results in the expected API calls.
        """
        self.api.get_zone_id('test.com')  # Implicitly calls _populate_zone_id_cache()
        self.assertEqual(len(self.api.client.domain.mock_calls), 4)
        self.api.client.domain.assert_has_calls([
            call.list('TEST_GANDI_API_KEY'),
            call.info('TEST_GANDI_API_KEY', 'test.com'),
            call.info('TEST_GANDI_API_KEY', 'example.com'),
            call.info('TEST_GANDI_API_KEY', 'opencraft.co.uk'),
        ], any_order=True)

    def test_split_domain_name(self):
        """
        Test that splitting domain names in subdomain and registered domain works correctly.
        """
        self.assertEqual(self.api.split_domain_name('sub.domain.test.com'), ('sub.domain', 'test.com'))
        self.assertEqual(self.api.split_domain_name('sub.domain.opencraft.co.uk'), ('sub.domain', 'opencraft.co.uk'))
        self.assertEqual(self.api.split_domain_name('example.com'), ('@', 'example.com'))
        with self.assertRaises(ValueError) as error:
            self.api.split_domain_name('sub.domain.unknown.com')
        self.assertEqual(
            str(error.exception),
            'The given domain name "sub.domain.unknown.com" does not match any domain registered in the Gandi account.'
        )

    def test_get_zone_id(self):
        """
        Gets zone_id for the requested FQDN.
        The zone_id is cached in memory after retreived for the first time.
        """
        self.populate_cache()
        zone_id = self.api.get_zone_id('test.com')
        self.assertEqual(zone_id, 9900)
        # There shouldn't be any API calls because the IDs are retrieved from the cache.
        self.assertEqual(len(self.api.client.domain.mock_calls), 0)

    def test_set_dns_record(self):
        """
        Set a DNS record value.
        """
        self.populate_cache()
        self.api.set_dns_record('sub.domain.test.com', type='A', value='192.168.99.99')
        self.assert_set_dns_record_calls()

    @patch('time.sleep')
    def test_set_dns_record_error_retry_and_succeed(self, sleep):
        """
        Test retry behaviour when setting a DNS record.  Succeed in the third attempt.
        """
        self.populate_cache()
        self.api.client.make_version_creation_fail(2)
        self.api.set_dns_record(
            'sub.domain.test.com',
            type='A', value='192.168.99.99'
        )
        self.assert_set_dns_record_calls(attempts=3)
        self.assertEqual(sleep.mock_calls, [call(1), call(2)])

    @patch('time.sleep')
    def test_set_dns_record_timeout_retry_and_fail(self, sleep):
        """
        Test retry behaviour returns timeout exception. Fail all attempts.
        """
        self.api.client.make_version_creation_fail(10, timeout=True)
        with self.assertRaises(TimeoutError):
            self.api.set_dns_record(
                'sub.domain.test.com',
                type='A', value='192.168.99.99'
            )
        self.assertEqual(sleep.mock_calls, [call(1), call(2), call(4)])

    @patch('time.sleep')
    def test_set_dns_record_error_retry_and_fail(self, sleep):
        """
        Test retry behaviour when setting a DNS record.  Fail all attempts.
        """
        self.api.client.make_version_creation_fail(10)
        with self.assertRaises(xmlrpc.client.Fault):
            self.api.set_dns_record(
                'sub.domain.test.com',
                type='A', value='192.168.99.99'
            )
        self.assertEqual(sleep.mock_calls, [call(1), call(2), call(4)])

    def test_remove_dns_record(self):
        """
        Test remove_dns_record().
        """
        self.populate_cache()
        self.api.remove_dns_record('sub.domain.test.com')
        self.assertEqual(self.api.client.domain.mock_calls, [
            call.zone.version.new('TEST_GANDI_API_KEY', 9900),
            call.zone.record.delete(
                'TEST_GANDI_API_KEY', 9900, 1,
                {'type': ['A', 'CNAME'], 'name': 'sub.domain'}
            ),
            call.zone.version.set('TEST_GANDI_API_KEY', 9900, 1),
        ])
