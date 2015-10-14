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
OpenStack - Tests
"""

# Imports #####################################################################

import requests

from collections import namedtuple
from unittest.mock import Mock, call, patch

from instance import openstack
from instance.tests.base import TestCase


# Tests #######################################################################

class OpenStackTestCase(TestCase):
    """
    Test cases for OpenStack helper functions
    """
    def setUp(self):
        super().setUp()

        self.nova = Mock()

    def test_create_server(self):
        """
        Create a VM via nova
        """
        self.nova.flavors.find.return_value = 'test-flavor'
        self.nova.images.find.return_value = 'test-image'
        openstack.create_server(self.nova, 'test-vm', {"ram": 4096, "disk": 40}, {"name": "Ubuntu 12.04"})
        self.assertEqual(self.nova.mock_calls, [
            call.flavors.find(disk=40, ram=4096),
            call.images.find(name='Ubuntu 12.04'),
            call.servers.create('test-vm', 'test-image', 'test-flavor', key_name=None)
        ])

    def test_delete_servers_by_name(self):
        """
        Delete all servers with a given name
        """
        server_class = namedtuple('server_class', 'name pk')
        self.nova.servers.list.return_value = [
            server_class(name='server-a', pk=1),
            server_class(name='server-a', pk=2),
            server_class(name='server-b', pk=3),
        ]
        openstack.delete_servers_by_name(self.nova, 'server-a')
        self.assertEqual(self.nova.mock_calls, [
            call.servers.list(),
            call.servers.delete(server_class(name='server-a', pk=1)),
            call.servers.delete(server_class(name='server-a', pk=2)),
        ])

    def test_get_server_public_address_none(self):
        """
        No public IP when none has been assigned yet
        """
        server_class = namedtuple('Server', 'addresses')
        server = server_class(addresses=[])
        self.assertEqual(openstack.get_server_public_address(server), None)

    @patch('requests.packages.urllib3.util.retry.Retry.sleep')
    @patch('http.client.HTTPConnection.getresponse')
    @patch('http.client.HTTPConnection.request')
    def test_nova_client_connection_error(self, mock_request, mock_getresponse, mock_retry_sleep):
        """
        Connection error during a request from the nova client
        Ensure requests are retried before giving up, with a backoff sleep between attempts
        """
        def getresponse_call(*args, **kwargs):
            """ Invoked by the nova client when making a HTTP request (via requests/urllib3) """
            raise ConnectionResetError('[Errno 104] Connection reset by peer')
        mock_getresponse.side_effect = getresponse_call
        nova = openstack.get_nova_client()
        with self.assertRaises(requests.exceptions.ConnectionError):
            nova.servers.get('test-id')
        self.assertEqual(mock_getresponse.call_count, 11)
        self.assertEqual(mock_retry_sleep.call_count, 10)
