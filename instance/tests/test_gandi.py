# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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

from instance import gandi
from instance.tests.base import TestCase


# Tests #######################################################################

class GandiTestCase(TestCase):
    """
    Test cases for Gandi API calls
    """
    def setUp(self):
        with patch('xmlrpc.client.ServerProxy'):
            self.api = gandi.GandiAPI()
            self.api.client.domain.zone.version.new.return_value = 'new_zone_version'

    @patch.multiple('instance.gandi.settings', GANDI_API_KEY='TEST_GANDI_API_KEY', GANDI_ZONE_ID=9900)
    def test_set_dns_record(self):
        """
        Set a DNS record value
        """
        self.api.set_dns_record(type='A', name='sub.domain', value='192.168.99.99')
        self.assertEqual(
            self.api.client.mock_calls,
            [
                call.domain.zone.version.new('TEST_GANDI_API_KEY', 9900),
                call.domain.zone.record.delete('TEST_GANDI_API_KEY', 9900, 'new_zone_version', {
                    'type': ['A', 'CNAME'],
                    'name': 'sub.domain',
                }),
                call.domain.zone.record.add('TEST_GANDI_API_KEY', 9900, 'new_zone_version', {
                    'value': '192.168.99.99',
                    'ttl': 1200,
                    'type': 'A',
                    'name': 'sub.domain',
                }),
                call.domain.zone.version.set('TEST_GANDI_API_KEY', 9900, 'new_zone_version')
            ]
        )
