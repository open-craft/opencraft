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

import http.client
import io

import novaclient
from mock import Mock, call, patch

from instance.models.server import OpenStackServer, Status as ServerStatus, Progress as ServerProgress
from instance.models.utils import SteadyStateException, WrongStateException
from instance.tests.base import AnyStringMatching, TestCase
from instance.tests.models.factories.instance import SingleVMOpenEdXInstanceFactory
from instance.tests.models.factories.server import (
    OpenStackServerFactory, BuildingOpenStackServerFactory, ReadyOpenStackServerFactory
)


# Tests #######################################################################

class MockHTTPResponse(http.client.HTTPResponse):
    """
    A fake http.client.HTTPResponse, for stubbing low-level urllib3 calls.
    """
    def __init__(self, status_code=200, body='{}'):
        content = 'HTTP/1.1 {status}\n\n{body}'.format(status=status_code, body=body).encode()
        sock = Mock()
        sock.makefile.return_value = io.BytesIO(content)
        super().__init__(sock)


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
        self.assertEqual(str(server), 'Pending OpenStack Server')
        self.assertEqual(server.status, ServerStatus.Pending)
        self.assertEqual(server.progress, ServerProgress.Running)

    @patch('instance.models.server.openstack.create_server')
    def test_start_server(self, mock_create_server):
        """
        Start a new server
        """
        mock_create_server.return_value.id = 'pending-server-id'
        server = OpenStackServerFactory()

        self.assertEqual(server.status, ServerStatus.Pending)
        self.assertEqual(server.progress, ServerProgress.Running)
        server.start()
        mock_create_server.assert_called_once_with(
            server.nova,
            AnyStringMatching(r'instance\d+\.test'),
            {"ram": 4096, "disk": 40},
            {"name": "Ubuntu 12.04"},
            key_name='opencraft',
        )

        server = OpenStackServer.objects.get(pk=server.pk)
        self.assertEqual(server.status, ServerStatus.Building)
        self.assertEqual(server.progress, ServerProgress.Success)
        self.assertEqual(server.openstack_id, 'pending-server-id')
        self.assertEqual(str(server), 'pending-server-id')

    @patch('instance.models.server.openstack.create_server')
    def test_os_server(self, mock_create_server):
        """
        Get the os_server attribute of a new server
        This should ensure the server is started to be able to return a value
        """
        mock_create_server.return_value.id = 'pending-server-id'
        server = OpenStackServerFactory()
        self.assertEqual(server.os_server, server.nova.servers.get.return_value)
        self.assertEqual(server.nova.mock_calls, [call.servers.get('pending-server-id')])

    @patch('novaclient.client.HTTPClient.authenticate', autospec=True)
    @patch('requests.packages.urllib3.connectionpool.HTTPConnection.response_class')
    @patch('instance.models.server.openstack.create_server')
    def test_os_server_nova_error(self, mock_create_server, mock_response_class, mock_authenticate):
        """
        The nova client should retry in case of server errors
        """
        mock_create_server.return_value.id = 'pending-server-id'
        mock_response_class.side_effect = (MockHTTPResponse(500),
                                           MockHTTPResponse(200, body='{"server": {}}'))

        def authenticate(client):
            """ Simulate nova client authentication """
            client.management_url = 'http://example.com'
        mock_authenticate.side_effect = authenticate

        # We do not use the OpenStackServerFactory here as it mocks the retry
        # behaviour that we are trying to test
        server = OpenStackServer.objects.create(instance=SingleVMOpenEdXInstanceFactory())
        self.assertTrue(server.os_server)

    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.time.sleep')
    def test_sleep_until_condition_already_fulfilled(self, mock_sleep, mock_update_status):
        """
        Check if sleep_until behaves correctly if condition to wait for
        is already fulfilled.
        """
        conditions = [
            lambda: server.status.is_steady_state,
            lambda: server.status.accepts_ssh_commands,
        ]
        for condition in conditions:
            server = OpenStackServerFactory()
            status_queue = [
                server._status_to_building,
                server._status_to_booting,
                server._status_to_ready,
            ]
            # Transition to state fulfilling condition
            for state_transition in status_queue:
                server._transition(state_transition, progress=ServerProgress.Success)

            # Sleep until condition is fulfilled.
            # Use a small value for "timeout" to ensure that we can fail quickly
            # if server can not reach desired status because transition logic is broken:
            server.sleep_until(condition, timeout=5)
            self.assertEqual(server.status, ServerStatus.Ready)
            self.assertEqual(server.progress, ServerProgress.Success)
            self.assertEqual(mock_sleep.call_count, 0)

    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.time.sleep')
    def test_sleep_until_state_changes(self, mock_sleep, mock_update_status):
        """
        Check if sleep_until behaves correctly if condition to wait for
        is unfulfilled initially.
        """
        conditions = [
            lambda: server.status.is_steady_state,
            lambda: server.status.accepts_ssh_commands,
        ]

        def scoped_update_status(server=None, status_queue=None):
            """ Return mock update_status scoped to a specific server and status_queue """
            def update_status():
                """ Simulate status progression """
                server._transition(status_queue.pop(), progress=ServerProgress.Success)
            return update_status

        for condition in conditions:
            server = OpenStackServerFactory()
            status_queue = [
                server._status_to_building,
                server._status_to_booting,
                server._status_to_ready,
            ]
            status_queue.reverse() # To be able to use pop()

            mock_update_status.side_effect = scoped_update_status(server, status_queue)
            mock_sleep.call_count = 0

            # Sleep until condition is fulfilled.
            # Use a small value for "timeout" to ensure that we can fail quickly
            # if server can not reach desired status because transition logic is broken:
            server.sleep_until(condition, timeout=5)
            self.assertEqual(server.status, ServerStatus.Ready)
            self.assertEqual(server.progress, ServerProgress.Success)
            self.assertEqual(mock_sleep.call_count, 2)

    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.Status.Building.is_steady_state')
    def test_sleep_until_steady_state(self, mock_building_is_steady_state, mock_update_status):
        """
        Check if sleep_until behaves correctly if condition to wait for
        can not be fulfilled because server is in a steady state
        (that doesn't fulfill the condition).
        """
        server = OpenStackServerFactory()

        def update_status():
            """ Simulate status progression """
            server._transition(server._status_to_building, progress=ServerProgress.Success)
        mock_update_status.side_effect = update_status

        # Pretend that Status.Building (which doesn't accept SSH commands) is a steady state
        mock_building_is_steady_state.return_value = True

        with self.assertRaises(SteadyStateException):
            # Try to sleep until condition is fulfilled.
            # Use a small value for "timeout" to ensure that we can fail quickly
            # if server can not reach desired status because transition logic is broken:
            server.sleep_until(lambda: server.status.accepts_ssh_commands, timeout=5)

    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.time.sleep')
    def test_sleep_until_timeout(self, mock_sleep, mock_update_status):
        """
        Check if sleep_until behaves correctly if condition to wait for
        is unfulfilled when timeout is reached.
        """
        server = OpenStackServerFactory()

        def update_status():
            """ Simulate status progression """
            server._transition(server._status_to_building, progress=ServerProgress.Success)
        mock_update_status.side_effect = update_status

        with self.assertRaises(TimeoutError):
            server.sleep_until(lambda: server.status.accepts_ssh_commands, timeout=1)
            self.assertEqual(mock_sleep.call_count, 1)

    def test_sleep_until_invalid_timeout(self):
        """
        Check if sleep_until behaves correctly when passed an invalid timeout value.
        """
        server = OpenStackServerFactory()

        for value in (-1, 0):
            with self.assertRaises(AssertionError):
                server.sleep_until(lambda: server.status.accepts_ssh_commands, timeout=value)

    @patch('instance.models.server.time.sleep')
    def test_reboot_ready_server(self, mock_sleep):
        """
        Reboot a server that has status 'ready'
        """
        server = ReadyOpenStackServerFactory()
        server.reboot()
        self.assertEqual(server.status, ServerStatus.Booting)
        server.os_server.reboot.assert_called_once_with(reboot_type='SOFT')
        mock_sleep.assert_called_once_with(30)

    def test_reboot_server_wrong_status(self):
        """
        Attempt to reboot a server while in a status that doesn't allow it
        """
        server = BuildingOpenStackServerFactory()
        with self.assertRaises(WrongStateException):
            server.reboot()

    def test_terminate_new_server(self):
        """
        Terminate a server with a 'new' status
        """
        server = OpenStackServerFactory()
        server.terminate()
        self.assertEqual(server.status, ServerStatus.Terminated)
        self.assertEqual(server.progress, ServerProgress.Success)
        server.terminate() # This shouldn't change anything
        self.assertEqual(server.status, ServerStatus.Terminated)
        self.assertEqual(server.progress, ServerProgress.Success)
        self.assertFalse(server.nova.mock_calls)

    def test_terminate_building_server(self):
        """
        Terminate a server with a 'building' status
        """
        server = BuildingOpenStackServerFactory()
        server.terminate()
        self.assertEqual(server.status, ServerStatus.Terminated)
        self.assertEqual(server.progress, ServerProgress.Success)
        server.os_server.delete.assert_called_once_with()

    def test_terminate_server_not_found(self):
        """
        Terminate a server for which the corresponding VM doesn't exist anymore
        """
        server = BuildingOpenStackServerFactory()

        def raise_not_found(): #pylint: disable=missing-docstring
            raise novaclient.exceptions.NotFound('not-found')
        server.os_server.delete.side_effect = raise_not_found
        server.logger = Mock()
        mock_logger = server.logger

        server.terminate()
        mock_logger.error.assert_called_once_with(AnyStringMatching('Error while attempting to terminate server'))
        self.assertEqual(server.status, ServerStatus.Terminated)
        self.assertEqual(server.progress, ServerProgress.Success)

    def test_public_ip_new_server(self):
        """
        A new server doesn't have a public IP
        """
        server = OpenStackServerFactory()
        self.assertEqual(server.public_ip, None)

    def test_public_ip_building_server(self):
        """
        A server in 'building' status doesn't have a public IP
        """
        server = BuildingOpenStackServerFactory(os_server_fixture='openstack/api_server_1_building.json')
        self.assertEqual(server.public_ip, None)

    def test_public_ip_active_server(self):
        """
        Get the public IP of an active server
        """
        server = BuildingOpenStackServerFactory(os_server_fixture='openstack/api_server_2_active.json')
        self.assertEqual(server.public_ip, '192.168.100.200')


class OpenStackServerStatusTestCase(TestCase):
    """
    Test cases for status switching in OpenStackServer models
    """
    # Factory boy doesn't properly support pylint+django
    #pylint: disable=no-member

    @patch('instance.models.server.openstack.create_server')
    def test_update_status_new(self, mock_create_server):
        """
        Update status while the server is new
        """
        mock_create_server.return_value.id = 'pending-server-id'
        server = OpenStackServerFactory(os_server_fixture='openstack/api_server_1_building.json')
        self.assertEqual(server.status, ServerStatus.Pending)
        self.assertEqual(server.progress, ServerProgress.Running)
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        self.assertEqual(server.progress, ServerProgress.Running)

    def test_update_status_building(self):
        """
        Update status while the server is building, without change on the OpenStack VM
        """
        server = BuildingOpenStackServerFactory(os_server_fixture='openstack/api_server_1_building.json')
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        self.assertEqual(server.progress, ServerProgress.Running)

    @patch('instance.models.server.is_port_open')
    def test_update_status_building_to_booting(self, mock_is_port_open):
        """
        Update status while the server is building, when the VM becomes active
        """
        mock_is_port_open.return_value = False
        server = BuildingOpenStackServerFactory(os_server_fixture='openstack/api_server_2_active.json')
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        self.assertEqual(server.status, ServerStatus.Booting)
        self.assertEqual(server.progress, ServerProgress.Success)

    @patch('instance.models.server.is_port_open')
    def test_update_status_booting_to_ready(self, mock_is_port_open):
        """
        Update status while the server is booting, when the VM becomes ready
        """
        server = BuildingOpenStackServerFactory(
            os_server_fixture='openstack/api_server_2_active.json',
            _status=ServerStatus.Booting.state_id)
        mock_is_port_open.return_value = False
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        mock_is_port_open.return_value = True
        self.assertIsInstance(server.update_status(), ServerStatus.Ready)
        self.assertEqual(server.status, ServerStatus.Ready)
        self.assertEqual(server.progress, ServerProgress.Success)

    @patch('instance.models.server.is_port_open')
    @patch('instance.models.server.time.sleep')
    def test_update_status_ready_to_booting(self, _mock_sleep, mock_is_port_open):
        """
        Update status when the server is rebooted
        """
        server = ReadyOpenStackServerFactory(
            os_server_fixture='openstack/api_server_2_active.json',
            _progress=ServerProgress.Success.state_id
        )
        # If server is in Status.Booting, update_status calls is_port_open
        # to determine if server should transition to Status.Ready.
        # When using a fixture for server.os_server, is_port_open will eventually return False,
        # but only after a delay of about two minutes.
        # So we mock out is_port_open here to speed up testing:
        mock_is_port_open.return_value = False
        self.assertIsInstance(server.update_status(), ServerStatus.Ready)
        self.assertEqual(server.progress, ServerProgress.Success)
        server.reboot()
        self.assertEqual(server.status, ServerStatus.Booting)
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        self.assertEqual(server.status, ServerStatus.Booting)
        self.assertEqual(server.progress, ServerProgress.Running)

    @patch('instance.models.server.is_port_open')
    def test_update_status_rebooting_to_ready(self, mock_is_port_open):
        """
        Update status while the server is rebooting, when the server becomes ready (ssh accessible again)
        """
        server = BuildingOpenStackServerFactory(
            os_server_fixture='openstack/api_server_2_active.json',
            _status=ServerStatus.Booting.state_id)
        mock_is_port_open.return_value = False
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        mock_is_port_open.return_value = True
        self.assertIsInstance(server.update_status(), ServerStatus.Ready)
        self.assertEqual(server.status, ServerStatus.Ready)
        self.assertEqual(server.progress, ServerProgress.Success)
