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
OpenStack Utilities - Tests
"""

# Imports #####################################################################

from collections import namedtuple
from unittest import mock
from unittest.mock import Mock, call, patch, MagicMock

import ddt
from django.conf import settings
from openstack.network.v2.security_group import SecurityGroup
from openstack.network.v2.security_group_rule import SecurityGroupRule
import requests
from swiftclient.service import SwiftError

from instance import openstack_utils
from instance.tests.base import TestCase

# Constants and helpers #######################################################

SecurityGroupRuleDefinition = openstack_utils.SecurityGroupRuleDefinition

CONTAINER_AUTH = dict(
    user='username',
    password='secret-password',
    tenant='123454321',
    auth_url='https://fii.bar.baz',
    region='GRA1',
)

CONTAINER_NAME = "test-container"

DOWNLOAD_FOLDER = '/var/cache/swift-download'

DOWNLOAD_FAILURE_EXTRAS = {
    'path': '/very/sweet/directory/cookie.txt',
    'pseudodir': False,
    'error': 'NeverSeenBeforeError',
    'traceback': '/down/the/rabbit/hole:42'
}


def create_file_download_response(success=True, status_code=200, container=CONTAINER_NAME):
    """Prepares a dict similar to ones returned by swift download operation."""
    file_download_response = {
        'success': success,
        'container': container,
        'response_dict': {
            'status': status_code
        }
    }
    if not success:
        file_download_response.update(
            DOWNLOAD_FAILURE_EXTRAS
        )

    return file_download_response


# Tests #######################################################################

@ddt.ddt
class OpenStackTestCase(TestCase):
    """
    Test cases for OpenStack helper functions
    """
    def setUp(self):
        super().setUp()

        self.nova = Mock()

    def test_get_openstack_connection(self):
        """
        Test get_openstack_connection()
        """
        conn = openstack_utils.get_openstack_connection("some_region")
        self.assertEqual(conn.profile.get_services()[0]['region_name'], "some_region")
        self.assertTrue(conn.session.user_agent.startswith('opencraft-im'))
        # TODO: In future we could use 'mimic' to fake the OpenStack API for testing.
        # Then, here we could test 'conn.authorize()'

    RULE1_DICT = {
        "direction": "egress", "ether_type": "IPv6", "protocol": None,
        "port_range_min": None, "port_range_max": None,
        "remote_ip_prefix": "::/0", "remote_group_id": None,
    }
    RULE2_DICT = {
        "direction": "ingress", "ether_type": "IPv4", "protocol": "tcp",
        "port_range_min": 22, "port_range_max": 22,
        "remote_ip_prefix": "0.0.0.0/0", "remote_group_id": None,
    }

    @ddt.data(
        # Case 1:
        (
            # Desired rules:
            [
                SecurityGroupRuleDefinition(**RULE2_DICT),
            ],
            # "Existing" rules on the mock OpenStack remote:
            [
                SecurityGroupRule.new(id="rule1", **RULE1_DICT),
            ],
            # Rules we expect to be added (as dicts):
            [RULE2_DICT],
            # IDs of rules we expect to be deleted:
            ["rule1"],
        ),
        # Case 2:
        (
            # Desired rules:
            [
                SecurityGroupRuleDefinition(**RULE1_DICT),
                SecurityGroupRuleDefinition(**RULE2_DICT),
            ],
            # "Existing" rules on the mock OpenStack remote:
            [
                SecurityGroupRule.new(id="rule2", **RULE2_DICT),
                SecurityGroupRule.new(id="rule3", **RULE2_DICT),  # Duplicate of rule 2
            ],
            # Rules we expect to be added (as dicts):
            [RULE1_DICT],
            # IDs of rules we expect to be deleted:
            ["rule3"],
        ),
        # Case 2:
        (
            # Desired rules:
            [
                SecurityGroupRuleDefinition(**RULE1_DICT),
                SecurityGroupRuleDefinition(**RULE2_DICT),
            ],
            # "Existing" rules on the mock OpenStack remote:
            [
                SecurityGroupRule.new(id="rule1", **RULE1_DICT),
                SecurityGroupRule.new(id="rule2", **RULE2_DICT),
            ],
            # Rules we expect to be added (as dicts):
            [],
            # IDs of rules we expect to be deleted:
            [],
        ),
    )
    @ddt.unpack
    def test_sync_security_group_rules(self, rule_definitions, existing_rules, expected_adds, expected_deletes):
        """
        Test sync_security_group_rules()
        """
        network = Mock()
        network.security_group_rules.return_value = existing_rules
        security_group = SecurityGroup.new(id="00000000-1234-1234-1234-000000000000")
        openstack_utils.sync_security_group_rules(security_group, rule_definitions, network=network)

        network.security_group_rules.assert_called_once_with(security_group_id=security_group.id)
        self.assertEqual(network.create_security_group_rule.call_count, len(expected_adds))
        add_call_kwargs = [c[1] for c in network.create_security_group_rule.call_args_list]
        for rule in add_call_kwargs:
            self.assertEqual(rule.pop("security_group_id"), security_group.id)
        self.assertEqual(add_call_kwargs, expected_adds)
        self.assertEqual(network.delete_security_group_rule.call_count, len(expected_deletes))
        deleted_ids = [c[0][0].id for c in network.delete_security_group_rule.call_args_list]
        self.assertEqual(deleted_ids, expected_deletes)

    def test_create_server(self):
        """
        Create a VM via nova
        """
        self.nova.flavors.find.return_value = 'test-flavor'
        self.nova.images.find.return_value = 'test-image'
        openstack_utils.create_server(self.nova, 'test-vm', {"ram": 4096, "disk": 40}, {"name": "Ubuntu 12.04"})
        self.assertEqual(self.nova.mock_calls, [
            call.flavors.find(disk=40, ram=4096),
            call.images.find(name='Ubuntu 12.04'),
            call.servers.create('test-vm', 'test-image', 'test-flavor', key_name=None, security_groups=None)
        ])

    @ddt.data(
        # Case 1: no public IP when none has been assigned yet
        ([], None),
        # Case 2: IPV4 address only
        (
            {
                'Ext-Net': [
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '137.74.25.16',
                        'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                        'version': 4,
                    },
                ],
            },
            {
                'OS-EXT-IPS:type': 'fixed',
                'addr': '137.74.25.16',
                'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                'version': 4,
            }
        ),
        # Case 3: IPV6 address only
        (
            {
                'Ext-Net': [
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '2001:41d0:302:1000::364',
                        'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                        'version': 6,
                    },
                ],
            },
            None
        ),
        # Case 4: IPV4 + IPV6 address
        (
            {
                'Ext-Net': [
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '2001:41d0:302:1000::364',
                        'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                        'version': 6,
                    },
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '137.74.25.16',
                        'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                        'version': 4,
                    },
                ],
            },
            {
                'OS-EXT-IPS:type': 'fixed',
                'addr': '137.74.25.16',
                'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                'version': 4,
            }
        ),
        # Case 5: IPV4 + IPV6 address, version 6 requested
        (
            {
                'Ext-Net': [
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '2001:41d0:302:1000::364',
                        'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                        'version': 6,
                    },
                    {
                        'OS-EXT-IPS:type': 'fixed',
                        'addr': '137.74.25.16',
                        'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                        'version': 4,
                    },
                ],
            },
            {
                'OS-EXT-IPS:type': 'fixed',
                'addr': '2001:41d0:302:1000::364',
                'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:30:12:4a',
                'version': 6,
            },
            6
        )
    )
    @ddt.unpack
    def test_get_server_public_address(self, addresses, expected_address, version=4):
        """
        Expect an address with the requested version, or None if not available.
        """
        server_class = namedtuple('Server', 'addresses')
        server = server_class(addresses=addresses)
        self.assertEqual(openstack_utils.get_server_public_address(server, ip_version=version), expected_address)

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
        nova = openstack_utils.get_nova_client(settings.OPENSTACK_REGION)
        with self.assertRaises(requests.exceptions.ConnectionError):
            nova.servers.get('test-id')
        self.assertEqual(mock_getresponse.call_count, 11)
        self.assertEqual(mock_retry_sleep.call_count, 10)


@ddt.ddt
class SwiftTestCase(TestCase):
    """Tests for various swift functions."""

    @classmethod
    def stat_container_response(cls, container_name=CONTAINER_NAME, read_acl='.r:*', write_acl='', size=0):
        """Response for swift stat call."""
        return {
            'headers': {
                'x-trans-id': 'tx3124', 'content-length': size,
                'accept-ranges': 'bytes',
                'date': 'Thu, 02 Jun 2016 14:07:11 GMT', 'x-container-read': read_acl,
                'x-timestamp': '1464279838.27942',
                'x-container-object-count': '0', 'content-type': 'text/plain; charset=utf-8',
                'connection': 'close',
                'x-storage-policy': 'Policy-0', 'x-container-bytes-used': size
            },
            'items': [
                ('Account', 'AUTH_foobarbaz'), ('Container', container_name),
                ('Objects', '0'), ('Bytes', size), ('Read ACL', read_acl), ('Write ACL', write_acl),
                ('Sync To', ''), ('Sync Key', '')
            ],
            'object': None, 'action': 'stat_container', 'success': True, 'container': container_name
        }

    def setUp(self):
        """Sets up mock for swift_service context manager."""
        self.service = MagicMock()
        self.service_handle = MagicMock()
        self.service_handle.__enter__.return_value = self.service
        self.swift_service_function = MagicMock(return_value=self.service_handle)
        self.swift_service_function_patch = mock.patch(
            "instance.openstack_utils.swift_service", self.swift_service_function
        )
        self.swift_service_function_patch.start()

    def tearDown(self):
        """Stops themock."""
        self.swift_service_function_patch.stop()

    def basic_checks(self, service_kwargs=None):
        """basic checks that check if swift_service was called with good parameters, and exited."""
        if service_kwargs is None:
            service_kwargs = {}

        # Checks if we opened service with proper credentials
        self.swift_service_function.assert_called_once_with(**service_kwargs)
        # Checks service was closed
        self.assertTrue(self.service_handle.__exit__.called)

    @ddt.data(
        CONTAINER_AUTH, {}
    )
    def test_create_swift_container(self, auth):
        """Test for create_swift_container function."""
        openstack_utils.create_swift_container(CONTAINER_NAME, **auth)
        self.service.post.assert_called_once_with(CONTAINER_NAME, options={'read_acl': '.r:*'})
        self.basic_checks(auth)

    @ddt.data(
        CONTAINER_AUTH, {}
    )
    def test_delete_swift_containerr(self, auth):
        """Test for delete_swift_container function."""
        self.service.delete.return_value = [None] * 10 # Response contents are ignored
        openstack_utils.delete_swift_container(CONTAINER_NAME, **auth)
        self.service.delete.assert_called_once_with(CONTAINER_NAME)
        self.basic_checks(auth)

    @ddt.data(
        # Two files downloaded successfully, no errors
        ({}, [{'success': True}, {'success': True}, ], []),
        # Two files downloaded successfully, no errors
        (CONTAINER_AUTH, [{'success': True}, {'success': True}, ], []),
        # Single failed download
        (
            {},
            [create_file_download_response(), create_file_download_response(False), ],
            [(CONTAINER_NAME, 1, 1 * [DOWNLOAD_FAILURE_EXTRAS]), ]
        ),
        # Two failed downloads
        (
            {},
            [create_file_download_response(False), create_file_download_response(False), ],
            [(CONTAINER_NAME, 2, 2 * [DOWNLOAD_FAILURE_EXTRAS]), ]
        ),
        # Many failures in different containers
        (
            {},
            [
                create_file_download_response(False, container="container-1"),
                create_file_download_response(False, container="container-1"),
                create_file_download_response(False, container="container-2"),
                create_file_download_response(True, container="container-1"),
                create_file_download_response(True, container="container-2"),
            ],
            [
                ("container-1", 2, 2 * [DOWNLOAD_FAILURE_EXTRAS]),
                ("container-2", 1, 1 * [DOWNLOAD_FAILURE_EXTRAS]),
            ]
        ),
        # Files that failed with 'Not Modified' status code are OK.
        (
            {},
            [
                create_file_download_response(False, status_code=304),
                create_file_download_response(False, status_code=304),
                create_file_download_response(False, status_code=304),
            ],
            []
        )

    )
    @ddt.unpack
    def test_download(self, auth, file_responses, expected_failed_files):
        """
        Test for download_swift_account function.
        :param dict auth: User authorization
        :param list[dict] file_responses: List of dicts, each dictionary corresponds
                          to a single response for downloaded file
        :param dict expected_failed_files: Expected response from the download call
        """
        self.service.download.return_value = file_responses
        actual_failed_files = openstack_utils.download_swift_account(DOWNLOAD_FOLDER, **auth)
        self.assertEqual(
            [tuple(failure) for failure in actual_failed_files],
            expected_failed_files
        )

    def test_download_propagates_exceptions(self):
        """
        Test that download raises all exceptions from Swift.
        """
        self.service.download.side_effect = SwiftError(None)
        with self.assertRaises(SwiftError):
            openstack_utils.download_swift_account(DOWNLOAD_FOLDER)

    @ddt.data(
        ({}, 'container-1', '1234', '.r:*'),
        (CONTAINER_AUTH, 'container-1', '1234', '.r:*'),
        (CONTAINER_AUTH, 'container-2', '0', ''),
        (CONTAINER_AUTH, 'container-2', '3', 'batman!'),
    )
    @ddt.unpack
    def test_stat_container(self, auth, container_name, size, read_acl):
        """Test for stat_container function. """
        self.service.stat.return_value = self.stat_container_response(
            container_name=container_name, size=size, read_acl=read_acl
        )
        actual_stat_response = openstack_utils.stat_container(container_name, **auth)
        self.service.stat.assert_called_once_with(container_name)
        self.assertEqual(read_acl, actual_stat_response.read_acl)
        self.assertEqual(size, actual_stat_response.bytes)
        self.basic_checks(auth)


@ddt.ddt
class ServicePassesAuthTestCase(TestCase):
    """Tests for swift_service call."""

    # pylint: disable=no-self-use
    def test_service_passes_auth(self):
        """Test if swift_service passes authorization properly. """
        with mock.patch('instance.openstack_utils.SwiftService') as service:
            openstack_utils.swift_service(
                user='user',
                password='password',
                tenant='tenant',
                auth_url='http://example.com/auth',
                region='Region'
            )

        service.assert_called_once_with(
            options={
                'auth_version': '2',
                'os_username': 'user',
                'os_password': 'password',
                'os_tenant_name':  'tenant',
                'os_auth_url': 'http://example.com/auth',
                'os_region_name': 'Region'
            }
        )
