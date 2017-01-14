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
OpenStackServer model - Tests
"""

# Imports #####################################################################

import http.client
import io
from unittest.mock import Mock, call, patch

from ddt import ddt, data, unpack
from django.conf import settings
import novaclient

from instance.models.server import OpenStackServer, Status as ServerStatus
from instance.models.utils import SteadyStateException, WrongStateException
from instance.tests.base import AnyStringMatching, TestCase
from instance.tests.models.factories.server import (
    OpenStackServerFactory,
    BootingOpenStackServerFactory,
    BuildingOpenStackServerFactory,
    BuildFailedOpenStackServerFactory,
    ReadyOpenStackServerFactory,
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


@ddt
class OpenStackServerTestCase(TestCase):
    """
    Test cases for OpenStackServer models
    """
    def test_new_server(self):
        """
        New OpenStackServer object
        """
        self.assertFalse(OpenStackServer.objects.all())
        server = OpenStackServerFactory()
        created_server = OpenStackServer.objects.get()
        self.assertEqual(created_server.pk, server.pk)
        self.assertIsInstance(created_server.status, ServerStatus.Pending)
        self.assertEqual(str(server), 'Pending OpenStack Server')
        self.assertEqual(server.status, ServerStatus.Pending)

    @patch('instance.models.server.openstack_utils.create_server')
    def test_start_server(self, mock_create_server):
        """
        Start a new server
        """
        mock_create_server.return_value.id = 'pending-server-id'
        server = OpenStackServerFactory()

        self.assertEqual(server.status, ServerStatus.Pending)
        server.start()
        mock_create_server.assert_called_once_with(
            server.nova,
            AnyStringMatching(r'test-inst-\d+'),
            settings.OPENSTACK_SANDBOX_FLAVOR,
            settings.OPENSTACK_SANDBOX_BASE_IMAGE,
            key_name=settings.OPENSTACK_SANDBOX_SSH_KEYNAME,
        )

        server = OpenStackServer.objects.get(pk=server.pk)
        self.assertEqual(server.status, ServerStatus.Building)
        self.assertEqual(server.openstack_id, 'pending-server-id')
        self.assertEqual(str(server), 'pending-server-id')

    @patch('instance.models.server.openstack_utils.create_server')
    def test_start_server_fails(self, mock_create_server):
        """
        Check if 'start' behaves correctly when server creation fails
        """
        mock_create_server.side_effect = novaclient.exceptions.ClientException(400)
        server = OpenStackServerFactory()

        self.assertEqual(server.status, ServerStatus.Pending)
        server.start()

        server = OpenStackServer.objects.get(pk=server.pk)
        self.assertEqual(server.status, ServerStatus.BuildFailed)

    @patch('instance.models.server.openstack_utils.create_server')
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
    @patch('instance.models.server.openstack_utils.create_server')
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
        server = OpenStackServer.objects.create(name_prefix="test-nova-error")
        self.assertTrue(server.os_server)

    @data(
        'is_steady_state',
        'accepts_ssh_commands',
        'vm_available',
    )
    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.time.sleep')
    def test_sleep_until_condition_already_fulfilled(self, condition, mock_sleep, mock_update_status):
        """
        Check if sleep_until behaves correctly if condition to wait for
        is already fulfilled.
        """
        server = OpenStackServerFactory()
        status_queue = [
            server._status_to_building,
            server._status_to_booting,
            server._status_to_ready,
        ]
        # Transition to state fulfilling condition
        for state_transition in status_queue:
            state_transition()

        # Sleep until condition is fulfilled.
        # Use a small value for "timeout" to ensure that we can fail quickly
        # if server can not reach desired status because transition logic is broken:
        server.sleep_until(lambda: getattr(server.status, condition), timeout=5)
        self.assertEqual(server.status, ServerStatus.Ready)
        self.assertEqual(mock_sleep.call_count, 0)

    @data(
        {
            'name': 'is_steady_state',
            'required_transitions': 3,
            'expected_status': ServerStatus.Ready,
        },
        {
            'name': 'accepts_ssh_commands',
            'required_transitions': 3,
            'expected_status': ServerStatus.Ready,
        },
        {
            'name': 'vm_available',
            'required_transitions': 2,
            'expected_status': ServerStatus.Booting,
        },
    )
    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.time.sleep')
    def test_sleep_until_state_changes(self, condition, mock_sleep, mock_update_status):
        """
        Check if sleep_until behaves correctly if condition to wait for
        is unfulfilled initially.
        """
        server = OpenStackServerFactory()
        status_queue = [
            server._status_to_building,
            server._status_to_booting,
            server._status_to_ready,
        ]
        status_queue.reverse() # To be able to use pop()

        def update_status():
            """ Simulate status progression """
            status_queue.pop()()

        mock_update_status.side_effect = update_status

        # Sleep until condition is fulfilled.
        # Use a small value for "timeout" to ensure that we can fail quickly
        # if server can not reach desired status because transition logic is broken:
        server.sleep_until(lambda: getattr(server.status, condition['name']), timeout=5)
        self.assertEqual(server.status, condition['expected_status'])
        self.assertEqual(mock_sleep.call_count, condition['required_transitions'] - 1)

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
            server._status_to_building()
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
            server._status_to_building()
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
    def test_reboot_booting_server(self, mock_sleep):
        """
        Reboot a server that has status 'booting'
        """
        server = BootingOpenStackServerFactory()
        server.reboot()
        self.assertEqual(server.status, ServerStatus.Booting)
        server.os_server.reboot.assert_not_called()
        mock_sleep.assert_not_called()

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

    @data(
        ServerStatus.Pending,
        ServerStatus.Building,
        ServerStatus.BuildFailed,
        ServerStatus.Terminated,
    )
    def test_reboot_server_wrong_status(self, server_status):
        """
        Attempt to reboot a server while in a status that doesn't allow it
        """
        server = OpenStackServerFactory(status=server_status)
        with self.assertRaises(WrongStateException):
            server.reboot()

    @data(
        ('building-server-id', ServerStatus.Building),
        ('booting-server-id', ServerStatus.Booting),
        ('ready-server-id', ServerStatus.Ready),
    )
    @unpack
    def test_vm_created(self, openstack_id, server_status):
        """
        Test that server correctly reports that a VM has been created for it
        """
        server = OpenStackServerFactory(openstack_id=openstack_id, status=server_status)
        self.assertTrue(server.vm_created)

    @data(
        ServerStatus.Pending,
        ServerStatus.Building,  # Edge case: Server has status 'building' but no OpenStack ID yet
        ServerStatus.BuildFailed,
        ServerStatus.Terminated,
    )
    def test_vm_not_created(self, server_status):
        """
        Test that server correctly reports that no VM has been created for it
        """
        server = OpenStackServerFactory(status=server_status)
        self.assertFalse(server.vm_created)

    @data(
        ('building-server-id', ServerStatus.Building),
        ('booting-server-id', ServerStatus.Booting),
        ('ready-server-id', ServerStatus.Ready),
    )
    @unpack
    def test_terminate_server_vm_created(self, openstack_id, server_status):
        """
        Terminate a server with a VM
        """
        server = OpenStackServerFactory(openstack_id=openstack_id, status=server_status)
        server.terminate()
        self.assertEqual(server.status, ServerStatus.Terminated)
        server.os_server.delete.assert_called_once_with()

    @data(
        ServerStatus.Pending,
        ServerStatus.Building,  # Edge case: Server has status 'building' but no OpenStack ID yet
        ServerStatus.BuildFailed,
        ServerStatus.Terminated,
    )
    def test_terminate_server_vm_unavailable(self, server_status):
        """
        Terminate a server without a VM
        """
        server = OpenStackServerFactory(status=server_status)
        try:
            server.terminate()
        except AssertionError:
            self.fail('Termination logic tried to operate on non-existent VM.')
        else:
            self.assertEqual(server.status, ServerStatus.Terminated)

    @data(
        ('booting-server-id', ServerStatus.Booting),
        ('ready-server-id', ServerStatus.Ready),
    )
    @unpack
    def test_terminate_server_not_found(self, openstack_id, server_status):
        """
        Terminate a server for which the corresponding VM doesn't exist anymore
        """
        server = OpenStackServerFactory(openstack_id=openstack_id, status=server_status)

        def raise_not_found(): #pylint: disable=missing-docstring
            raise novaclient.exceptions.NotFound('not-found')
        server.os_server.delete.side_effect = raise_not_found
        server.logger = Mock()
        mock_logger = server.logger

        server.terminate()
        self.assertEqual(server.status, ServerStatus.Terminated)
        server.os_server.delete.assert_called_once_with()
        mock_logger.error.assert_called_once_with(AnyStringMatching('Error while attempting to terminate server'))

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


@ddt
class OpenStackServerStatusTestCase(TestCase):
    """
    Test cases for status switching in OpenStackServer models
    """
    def _assert_status_conditions(self, server, is_steady_state=False, accepts_ssh_commands=False, vm_available=False):
        """
        Assert that status conditions for server hold as specified
        """
        self.assertEqual(server.status.is_steady_state, is_steady_state)
        self.assertEqual(server.status.accepts_ssh_commands, accepts_ssh_commands)
        self.assertEqual(server.status.vm_available, vm_available)

    def test_status_transitions(self):
        """
        Test that status transitions work as expected for different server workflows
        """
        # Normal workflow
        server = OpenStackServerFactory()
        self.assertEqual(server.status, ServerStatus.Pending)
        self._assert_status_conditions(server)

        server._status_to_building()
        self.assertEqual(server.status, ServerStatus.Building)
        self._assert_status_conditions(server)

        server._status_to_unknown()
        self.assertEqual(server.status, ServerStatus.Unknown)
        self._assert_status_conditions(server)

        server._status_to_building()
        self.assertEqual(server.status, ServerStatus.Building)
        self._assert_status_conditions(server)

        server._status_to_booting()
        self.assertEqual(server.status, ServerStatus.Booting)
        self._assert_status_conditions(server, vm_available=True)

        server._status_to_unknown()
        self.assertEqual(server.status, ServerStatus.Unknown)
        self._assert_status_conditions(server)

        server._status_to_booting()
        self.assertEqual(server.status, ServerStatus.Booting)
        self._assert_status_conditions(server, vm_available=True)

        server._status_to_ready()
        self.assertEqual(server.status, ServerStatus.Ready)
        self._assert_status_conditions(server, is_steady_state=True, accepts_ssh_commands=True, vm_available=True)

        server._status_to_unknown()
        self.assertEqual(server.status, ServerStatus.Unknown)
        self._assert_status_conditions(server)

        server._status_to_ready()
        self.assertEqual(server.status, ServerStatus.Ready)
        self._assert_status_conditions(server, is_steady_state=True, accepts_ssh_commands=True, vm_available=True)

        server._status_to_terminated()
        self.assertEqual(server.status, ServerStatus.Terminated)
        self._assert_status_conditions(server, is_steady_state=True)

        # Server creation fails
        instance_bad_server = BuildingOpenStackServerFactory()
        instance_bad_server._status_to_build_failed()
        self.assertEqual(instance_bad_server.status, ServerStatus.BuildFailed)
        self._assert_status_conditions(server, is_steady_state=True)

    @data(
        {
            'name': '_status_to_building',
            'from_states': [
                ServerStatus.Pending,
                ServerStatus.Unknown
            ],
        },
        {
            'name': '_status_to_build_failed',
            'from_states': [
                ServerStatus.Building,
                ServerStatus.Unknown
            ],
        },
        {
            'name': '_status_to_booting',
            'from_states': [
                ServerStatus.Building,
                ServerStatus.Ready,
                ServerStatus.Unknown,
            ],
        },
        {
            'name': '_status_to_ready',
            'from_states': [
                ServerStatus.Booting,
                ServerStatus.Unknown
            ],
        },
        {
            'name': '_status_to_terminated',
            'from_states': ServerStatus.states,
        },
        {
            'name': '_status_to_unknown',
            'from_states': [
                ServerStatus.Building,
                ServerStatus.Booting,
                ServerStatus.Ready,
                ServerStatus.Unknown,
            ],
        },
    )
    def test_invalid_status_transitions(self, transition):
        """
        Test that invalid status transitions raise exception
        """
        # TODO: Get pylint to see state as an iterable
        invalid_from_states = (state for state in ServerStatus.states #pylint: disable=not-an-iterable
                               if state not in transition['from_states'])
        for invalid_from_state in invalid_from_states:
            instance = OpenStackServerFactory(status=invalid_from_state)
            self.assertEqual(instance.status, invalid_from_state)
            with self.assertRaises(WrongStateException):
                getattr(instance, transition['name'])()

    @patch('instance.models.server.openstack_utils.create_server')
    def test_update_status_pending(self, mock_create_server):
        """
        Update status while the server is pending
        """
        mock_create_server.return_value.id = 'pending-server-id'
        server = OpenStackServerFactory()
        self.assertEqual(server.status, ServerStatus.Pending)
        self.assertIsInstance(server.update_status(), ServerStatus.Building)
        self.assertEqual(server.status, ServerStatus.Building)

    def test_update_status_building(self):
        """
        Update status while the server is building, without change on the OpenStack VM
        """
        server = BuildingOpenStackServerFactory(os_server_fixture='openstack/api_server_1_building.json')
        self.assertEqual(server.status, ServerStatus.Building)
        self.assertIsInstance(server.update_status(), ServerStatus.Building)
        self.assertEqual(server.status, ServerStatus.Building)

    def test_update_status_build_failed(self):
        """
        Update status while not being able to interact with the server
        """
        server = BuildFailedOpenStackServerFactory()
        self.assertEqual(server.status, ServerStatus.BuildFailed)
        self.assertIsInstance(server.update_status(), ServerStatus.BuildFailed)
        self.assertEqual(server.status, ServerStatus.BuildFailed)
        self.assertFalse(server.nova.mock_calls)

    @patch('instance.models.server.is_port_open')
    def test_update_status_building_to_booting(self, mock_is_port_open):
        """
        Update status while the server is building, when the VM becomes active
        """
        mock_is_port_open.return_value = False
        server = BuildingOpenStackServerFactory(os_server_fixture='openstack/api_server_2_active.json')
        self.assertEqual(server.status, ServerStatus.Building)
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        self.assertEqual(server.status, ServerStatus.Booting)

    @patch('instance.models.server.is_port_open')
    def test_update_status_booting_to_ready(self, mock_is_port_open):
        """
        Update status while the server is booting, when the VM becomes ready
        """
        server = BootingOpenStackServerFactory(os_server_fixture='openstack/api_server_2_active.json')
        self.assertEqual(server.status, ServerStatus.Booting)
        mock_is_port_open.return_value = False
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        self.assertEqual(server.status, ServerStatus.Booting)
        mock_is_port_open.return_value = True
        self.assertIsInstance(server.update_status(), ServerStatus.Ready)
        self.assertEqual(server.status, ServerStatus.Ready)

    @patch('instance.models.server.is_port_open')
    @patch('instance.models.server.time.sleep')
    def test_update_status_ready_to_booting(self, _mock_sleep, mock_is_port_open):
        """
        Update status when the server is rebooted
        """
        server = ReadyOpenStackServerFactory(os_server_fixture='openstack/api_server_2_active.json')
        # If server is in Status.Booting, update_status calls is_port_open
        # to determine if server should transition to Status.Ready.
        # When using a fixture for server.os_server, is_port_open will eventually return False,
        # but only after a delay of about two minutes.
        # So we mock out is_port_open here to speed up testing:
        mock_is_port_open.return_value = False
        self.assertEqual(server.status, ServerStatus.Ready)
        self.assertIsInstance(server.update_status(), ServerStatus.Ready)
        server.reboot()
        self.assertEqual(server.status, ServerStatus.Booting)
        self.assertIsInstance(server.update_status(), ServerStatus.Booting)
        self.assertEqual(server.status, ServerStatus.Booting)
