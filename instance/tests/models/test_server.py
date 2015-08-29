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
OpenStackServer model - Tests
"""

# Imports #####################################################################

import novaclient
from mock import Mock, call, patch

from instance.models.server import OpenStackServer, ServerNotReady
from instance.tests.base import AnyStringMatching, TestCase
from instance.tests.models.factories.server import OpenStackServerFactory, StartedOpenStackServerFactory


# Tests #######################################################################

class OpenStackServerTestCase(TestCase):
    """
    Test cases for OpenStackServer models
    """
    # Factory boy doesn't properly support pylint+django
    #pylint: disable=no-member

    def test_new_server(self):
        """
        New OpenStackServer object
        """
        self.assertFalse(OpenStackServer.objects.all())
        server = OpenStackServerFactory()
        self.assertEqual(OpenStackServer.objects.get().pk, server.pk)
        self.assertEqual(str(server), 'New OpenStack Server')
        self.assertEqual(server.status, server.NEW)

    @patch('instance.models.server.openstack.create_server')
    def test_start_server(self, mock_create_server):
        """
        Start a new server
        """
        mock_create_server.return_value.id = 'new-server-id'
        server = OpenStackServerFactory()

        self.assertEqual(server.status, server.NEW)
        server.start()
        mock_create_server.assert_called_once_with(
            server.nova,
            AnyStringMatching(r'instance\d+\.test'),
            {"ram": 4096, "disk": 40},
            {"name": "Ubuntu 12.04"},
            key_name='opencraft',
        )

        server = OpenStackServer.objects.get(pk=server.pk)
        self.assertEqual(server.status, server.STARTED)
        self.assertEqual(server.openstack_id, 'new-server-id')
        self.assertEqual(str(server), 'new-server-id')

    @patch('instance.models.server.openstack.create_server')
    def test_os_server(self, mock_create_server):
        """
        Get the os_server attribute of a new server
        This should ensure the server is started to be able to return a value
        """
        mock_create_server.return_value.id = 'new-server-id'
        server = OpenStackServerFactory()
        self.assertEqual(server.os_server, server.nova.servers.get.return_value)
        self.assertEqual(server.nova.mock_calls, [call.servers.get('new-server-id')])

    @patch('instance.models.server.openstack.create_server')
    def test_update_status_new(self, mock_create_server):
        """
        Update status while the server is new
        """
        mock_create_server.return_value.id = 'new-server-id'
        server = OpenStackServerFactory(os_server_fixture='openstack/api_server_1_building.json')
        self.assertEqual(server.update_status(), server.STARTED)
        self.assertEqual(server.status, server.STARTED)
        self.assertEqual(server.update_status(), server.STARTED)
        self.assertEqual(server.status, server.STARTED)

    def test_update_status_started(self):
        """
        Update status while the server is started, without change on the OpenStack VM
        """
        server = StartedOpenStackServerFactory(os_server_fixture='openstack/api_server_1_building.json')
        self.assertEqual(server.update_status(), server.STARTED)
        self.assertEqual(server.status, server.STARTED)

    @patch('instance.models.server.is_port_open')
    def test_update_status_started_to_active(self, mock_is_port_open):
        """
        Update status while the server is started, when the VM becomes active
        """
        mock_is_port_open.return_value = False
        server = StartedOpenStackServerFactory(os_server_fixture='openstack/api_server_2_active.json')
        self.assertEqual(server.update_status(), server.ACTIVE)
        self.assertEqual(server.status, server.ACTIVE)

    @patch('instance.models.server.is_port_open')
    def test_update_status_active_to_booted(self, mock_is_port_open):
        """
        Update status while the server is active, when the VM becomes booted
        """
        server = StartedOpenStackServerFactory(
            os_server_fixture='openstack/api_server_2_active.json',
            status=OpenStackServer.ACTIVE)
        mock_is_port_open.return_value = False
        self.assertEqual(server.update_status(), server.ACTIVE)
        mock_is_port_open.return_value = True
        self.assertEqual(server.update_status(), server.BOOTED)
        self.assertEqual(server.status, server.BOOTED)

    def test_update_status_booted_to_provisioned(self):
        """
        Update status while the server is booted, when the VM is provisioned
        """
        server = StartedOpenStackServerFactory(
            os_server_fixture='openstack/api_server_2_active.json',
            status=OpenStackServer.BOOTED)
        self.assertEqual(server.update_status(), server.BOOTED)
        self.assertEqual(server.update_status(provisioned=True), server.PROVISIONED)
        self.assertEqual(server.status, server.PROVISIONED)

    def test_update_status_provisioned_to_rebooting(self):
        """
        Update status when the server is rebooted, after being provisioned
        """
        server = StartedOpenStackServerFactory(
            os_server_fixture='openstack/api_server_2_active.json',
            status=OpenStackServer.PROVISIONED)
        self.assertEqual(server.update_status(), server.PROVISIONED)
        self.assertEqual(server.update_status(rebooting=True), server.REBOOTING)
        self.assertEqual(server.status, server.REBOOTING)

    @patch('instance.models.server.is_port_open')
    def test_update_status_rebooting_to_ready(self, mock_is_port_open):
        """
        Update status while the server is rebooting, when the server becomes ready (ssh accessible again)
        """
        server = StartedOpenStackServerFactory(
            os_server_fixture='openstack/api_server_2_active.json',
            status=OpenStackServer.REBOOTING)
        mock_is_port_open.return_value = False
        self.assertEqual(server.update_status(), server.REBOOTING)
        mock_is_port_open.return_value = True
        self.assertEqual(server.update_status(), server.READY)
        self.assertEqual(server.status, server.READY)

    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.time.sleep')
    def test_sleep_until_status(self, mock_sleep, mock_update_status):
        """
        Sleep until the server gets to 'booted' status (single status string argument)
        """
        server = OpenStackServerFactory()
        status_queue = [server.STARTED, server.STARTED, server.ACTIVE, server.BOOTED, server.TERMINATED]
        status_queue.reverse() # To be able to use pop()

        def update_status():
            """ Simulate status progression successive runs """
            server.status = status_queue.pop()
        mock_update_status.side_effect = update_status

        self.assertEqual(server.sleep_until_status(server.BOOTED), server.BOOTED)
        self.assertEqual(server.status, server.BOOTED)
        self.assertEqual(mock_sleep.call_count, 3)
        self.assertEqual(status_queue, [server.TERMINATED])

    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.time.sleep')
    def test_sleep_until_status_list(self, mock_sleep, mock_update_status):
        """
        Sleep until the server gets to one of the status in a list
        """
        server = OpenStackServerFactory()
        status_queue = [server.STARTED, server.BOOTED]
        status_queue.reverse() # To be able to use pop()

        def update_status():
            """ Simulate status progression successive runs """
            server.status = status_queue.pop()
        mock_update_status.side_effect = update_status

        self.assertEqual(server.sleep_until_status([server.TERMINATED, server.BOOTED]), server.BOOTED)
        self.assertEqual(server.status, server.BOOTED)

    @patch('instance.models.server.time.sleep')
    def test_reboot_provisioned_server(self, mock_sleep):
        """
        Reboot a provisioned server
        """
        server = StartedOpenStackServerFactory(status=OpenStackServer.PROVISIONED)
        server.reboot()
        self.assertEqual(server.status, server.REBOOTING)
        server.os_server.reboot.assert_called_once_with(reboot_type='SOFT')
        mock_sleep.assert_called_once_with(30)

    def test_reboot_server_wrong_status(self):
        """
        Attempt to reboot a server while in a status that doesn't allow it
        """
        server = StartedOpenStackServerFactory()
        with self.assertRaises(ServerNotReady):
            server.reboot()

    def test_terminate_new_server(self):
        """
        Terminate a server with a 'new' status
        """
        server = OpenStackServerFactory()
        server.terminate()
        self.assertEqual(server.status, server.TERMINATED)
        server.terminate() # This shouldn't change anything
        self.assertEqual(server.status, server.TERMINATED)
        self.assertFalse(server.nova.mock_calls)

    def test_terminate_started_server(self):
        """
        Terminate a server with a 'started' status
        """
        server = StartedOpenStackServerFactory()
        server.terminate()
        self.assertEqual(server.status, server.TERMINATED)
        server.os_server.delete.assert_called_once_with()

    def test_terminate_server_not_found(self):
        """
        Terminate a server for which the corresponding VM doesn't exist anymore
        """
        server = StartedOpenStackServerFactory()

        def raise_not_found(): #pylint: disable=missing-docstring
            raise novaclient.exceptions.NotFound('not-found')
        server.os_server.delete.side_effect = raise_not_found
        server.logger = Mock()
        mock_logger = server.logger

        server.terminate()
        mock_logger.error.assert_called_once_with(AnyStringMatching('Error while attempting to terminate server'))
        self.assertEqual(server.status, server.TERMINATED)

    def test_public_ip_new_server(self):
        """
        A new server doesn't have a public IP
        """
        server = OpenStackServerFactory()
        self.assertEqual(server.public_ip, None)

    def test_public_ip_started_server(self):
        """
        A server in `started` status doesn't have a public IP
        """
        server = StartedOpenStackServerFactory(os_server_fixture='openstack/api_server_1_building.json')
        self.assertEqual(server.public_ip, None)

    def test_public_ip_active_server(self):
        """
        Get the public IP of an active server
        """
        server = StartedOpenStackServerFactory(os_server_fixture='openstack/api_server_2_active.json')
        self.assertEqual(server.public_ip, '192.168.100.200')
