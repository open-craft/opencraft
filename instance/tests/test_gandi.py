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
Gandi - Tests
"""

# Imports #####################################################################

from unittest.mock import call, MagicMock, patch

from django.conf import settings

from instance import gandi
from instance.gandi import GandiV5API
from instance.tests.base import TestCase


# Tests #######################################################################


class GandiV5TestCase(TestCase):
    """
    Test cases for Gandi V5 API calls.
    """

    def setUp(self):
        super().setUp()
        self.api = gandi.GandiV5API(api_key='api-key')

    def populate_domain_cache(self):
        """
        Populate the domain cache of the API client.
        """
        self.api._domain_cache = ['test.com', 'opencraft.co.uk', 'example.com']

    @patch('instance.gandi.requests.get')
    def test_populate_domain_cache(self, mocked_get):
        """
        Test that populating the domain cache results in the expected API calls.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = [{'fqdn': 'test.com'}, {'fqdn': 'example.com'}]
        mocked_get.return_value = mock_response
        self.api._populate_domain_cache()
        assert self.api._domain_cache == ['test.com', 'example.com']

    @patch('instance.gandi.requests.get')
    def test_populate_domain_cache_empty_result_from_api_call(self, mocked_get):
        """
        Test that settings.GANDI_DEFAULT_BASE_DOMAIN is added to the domain cache when the API
        returns an empty list of domains.
        """
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mocked_get.return_value = mock_response
        self.api._populate_domain_cache()
        assert self.api._domain_cache == [settings.GANDI_DEFAULT_BASE_DOMAIN]

    def test_split_domain_name(self):
        """
        Test that splitting domain names in subdomain and registered domain works correctly.
        """
        self.populate_domain_cache()
        self.assertEqual(self.api._split_domain_name('sub.domain.test.com'), ('sub.domain', 'test.com'))
        self.assertEqual(self.api._split_domain_name('sub.domain.opencraft.co.uk'), ('sub.domain', 'opencraft.co.uk'))
        self.assertEqual(self.api._split_domain_name('example.com'), ('@', 'example.com'))
        with self.assertRaises(ValueError) as error:
            self.api._split_domain_name('sub.domain.unknown.com')
        self.assertEqual(
            str(error.exception),
            'The given domain name "sub.domain.unknown.com" does not match any domain registered in the Gandi account.'
        )

    @patch('instance.gandi.cache')
    @patch('lexicon.client.Client.execute')
    def test_list_dns_record_no_cache(self, mocked_lexicon_client_execute, mocked_cache):
        """
        Test listing all DNS records for a domain.
        """
        mocked_cache.get.return_value = None
        mocked_lexicon_client_execute.return_value = []

        self.populate_domain_cache()
        self.api.list_dns_records(dict(domain='test.com', type='CNAME'))
        self.assertEqual(mocked_lexicon_client_execute.call_count, 1)
        mocked_cache.set.assert_called_once_with('test.com-CNAME', [])

    @patch.object(GandiV5API, 'list_dns_records')
    def test_filter_dns_record_default_cname(self, mocked_list_dns_records):
        """
        Test filtering DNS records for a domain.
        """
        expected_domain = 'test.com'
        mocked_list_dns_records.return_value = []
        self.populate_domain_cache()
        self.api.filter_dns_records(expected_domain)
        mocked_list_dns_records.assert_called_once_with(dict(domain=expected_domain, type='CNAME'))

    @patch.object(GandiV5API, 'list_dns_records')
    def test_filter_dns_record_with_an_a_record(self, mocked_list_dns_records):
        """
        Test filtering DNS records for a domain.
        """
        expected_domain = 'test.com'
        expected_type = 'A'
        mocked_list_dns_records.return_value = []
        self.populate_domain_cache()
        self.api.filter_dns_records(expected_domain, type=expected_type)
        mocked_list_dns_records.assert_called_once_with(dict(domain=expected_domain, type=expected_type))

    @patch('lexicon.client.Client.execute')
    def test_set_dns_record(self, mocked_lexicon_client_execute):
        """
        Test setting a DNS record calls the expected library method.
        """
        mocked_lexicon_client_execute.return_value = True
        self.populate_domain_cache()
        self.api.set_dns_record('sub.domain.test.com', type='A', value='1.2.3.4')
        assert mocked_lexicon_client_execute.call_count == 2

    @patch('instance.gandi.cache')
    @patch('lexicon.client.Client.execute')
    def test_set_dns_record_invalidates_cache(self, mocked_lexicon_client_execute, mocked_cache):
        """
        Test adding a DNS record invalidates the cache.
        """
        mocked_lexicon_client_execute.return_value = []
        self.populate_domain_cache()

        self.api.set_dns_record('sub.domain.test.com', type='A', value='1.2.3.4')

        mocked_cache.delete.has_calls([
            call('test.com-A'),  # Called by deleting the existing record
            call('test.com-A'),  # Called by setting the new record
        ])

    @patch.object(GandiV5API, 'add_dns_record')
    @patch.object(GandiV5API, 'delete_dns_record')
    def test_set_dns_record_calls_delete_and_add_methods(self, mocked_delete_method, mocked_add_method):
        """
        Test setting a DNS record calls the delete record method and the add record method.
        """
        mocked_delete_method.return_value = True
        mocked_add_method.return_value = True
        self.populate_domain_cache()
        self.api.set_dns_record('sub.domain.test.com', type='A', value='1.2.3.4')
        mocked_delete_method.assert_called_once()
        mocked_add_method.assert_called_once()
        expected_call_args = {'name': 'sub.domain', 'domain': 'test.com', 'type': 'A', 'value': '1.2.3.4', 'ttl': 1200}
        assert mocked_delete_method.call_args_list == [call(expected_call_args)]
        assert mocked_add_method.call_args_list == [call(expected_call_args)]


    @patch.object(GandiV5API, 'add_dns_record')
    @patch.object(GandiV5API, 'delete_dns_record')
    @patch('time.sleep')
    def test_set_dns_record_error_retry_and_succeed(self, mocked_sleep, mocked_delete, mocked_add):
        """
        Test retry behaviour when setting a DNS record. Succeed in the fourth attempt.
        """
        mocked_delete.return_value = True
        mocked_add.side_effect = [Exception(), Exception(), Exception(), True]
        self.populate_domain_cache()
        self.api.set_dns_record('sub.domain.test.com', type='A', value='1.2.3.4')
        assert mocked_delete.call_count == 4
        assert mocked_add.call_count == 4

    @patch.object(GandiV5API, 'add_dns_record')
    @patch.object(GandiV5API, 'delete_dns_record')
    @patch('time.sleep')
    def test_set_dns_record_error_retry_and_fail(self, mocked_sleep, mocked_delete, mocked_add):
        """
        Test retry behaviour raises an Exception when all retry attempts have failed.
        """
        mocked_delete.return_value = True
        mocked_add.side_effect = [Exception(), Exception(), Exception(), Exception()]
        self.populate_domain_cache()
        with self.assertRaises(Exception):
            self.api.set_dns_record('sub.domain.test.com', type='A', value='1.2.3.4')
        assert mocked_delete.call_count == 4
        assert mocked_add.call_count == 4

    @patch.object(GandiV5API, 'delete_dns_record')
    def test_remove_dns_record(self, mocked_delete):
        """
        Test removing a DNS record.
        """
        mocked_delete.return_value = True
        self.populate_domain_cache()
        self.api.remove_dns_record('sub.domain.test.com', type='A', value='1.2.3.4')
        mocked_delete.assert_called_once()
        expected_call_args = {'name': 'sub.domain', 'domain': 'test.com', 'type': 'A', 'value': '1.2.3.4'}
        assert mocked_delete.call_args_list == [call(expected_call_args)]

    @patch('instance.gandi.cache')
    @patch('lexicon.client.Client.execute')
    def test_remove_dns_record_invalidates_cache(self, mocked_lexicon_client_execute, mocked_cache):
        """
        Test removing a DNS record invalidates the cache.
        """
        mocked_lexicon_client_execute.return_value = []
        self.populate_domain_cache()

        self.api.remove_dns_record('sub.domain.test.com', type='A', value='1.2.3.4')

        mocked_cache.delete.assert_called_once_with('test.com-A')
