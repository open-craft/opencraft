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

from collections import namedtuple
from unittest.mock import call, Mock

from instance import openstack
from instance.tests.base import TestCase


# Tests #######################################################################

class OpenStackTestCase(TestCase):
    """
    Test cases for OpenStack helper functions
    """
    def setUp(self):
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

    def test_get_server_public_address(self):
        """
        Get public IP of a server
        """
        server_class = namedtuple('Server', 'addresses')
        server = server_class(addresses={'a': ['192.168.99.88']})
        self.assertEqual(openstack.get_server_public_address(server), '192.168.99.88')

    def test_get_server_public_address_none(self):
        """
        No public IP when none has been assigned yet
        """
        server_class = namedtuple('Server', 'addresses')
        server = server_class(addresses=[])
        self.assertEqual(openstack.get_server_public_address(server), None)
