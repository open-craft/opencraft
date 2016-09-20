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
Views - Tests
"""

# Imports #####################################################################

from unittest.mock import patch
import ddt

from rest_framework import status

from instance.tests.api.base import APITestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory


# Tests #######################################################################

@ddt.ddt
class OpenEdXAppServerAPITestCase(APITestCase):
    """
    Test cases for OpenEdXAppServer API calls
    """
    def test_get_unauthenticated(self):
        """
        GET - Require to be authenticated
        """
        response = self.api_client.get('/api/v1/openedx_appserver/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    @ddt.data(
        'user1', 'user2',
    )
    def test_get_permission_denied(self, username):
        """
        GET - basic and staff users denied access
        """
        self.api_client.login(username=username, password='pass')
        response = self.api_client.get('/api/v1/openedx_appserver/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "You do not have permission to perform this action."})

    def test_get_authenticated(self):
        """
        GET - Authenticated - instance manager users allowed access
        """
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/openedx_appserver/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        app_server = make_test_appserver()
        response = self.api_client.get('/api/v1/openedx_appserver/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data[0].items()
        self.assertIn(('id', app_server.pk), data)
        self.assertIn(('api_url', 'http://testserver/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk)), data)
        self.assertIn(('name', 'AppServer 1'), data)
        # Status fields:
        self.assertIn(('status', 'new'), data)
        self.assertIn(('status_name', 'New'), data)
        self.assertIn(('status_description', 'Newly created'), data)
        self.assertIn(('is_steady', True), data)
        self.assertIn(('is_healthy', True), data)
        # Created/modified date:
        self.assertIn('created', response.data[0])
        self.assertIn('modified', response.data[0])
        # Other details should not be in the list view:
        self.assertNotIn('instance', response.data[0])
        self.assertNotIn('server', response.data[0])
        self.assertNotIn('configuration_settings', response.data[0])
        self.assertNotIn('edx_platform_commit', response.data[0])
        self.assertNotIn('log_entries', response.data[0])
        self.assertNotIn('log_error_entries', response.data[0])

    @ddt.data(
        (None, 'Authentication credentials were not provided.'),
        ('user1', 'You do not have permission to perform this action.'),
        ('user2', 'You do not have permission to perform this action.'),
    )
    @ddt.unpack
    def test_get_details_permission_denied(self, username, message):
        """
        GET - Detailed attributes - anonymous, basic, and staff users denied access
        """
        if username:
            self.api_client.login(username=username, password='pass')
        app_server = make_test_appserver()
        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': message})

    def test_get_details(self):
        """
        GET - Detailed attributes - instance manager allowed access
        """
        self.api_client.login(username='user3', password='pass')
        app_server = make_test_appserver()
        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data.items()
        self.assertIn(('id', app_server.pk), data)
        self.assertIn(('api_url', 'http://testserver/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk)), data)
        self.assertIn(('name', 'AppServer 1'), data)
        # Status fields:
        self.assertIn(('status', 'new'), data)
        self.assertIn(('status_name', 'New'), data)
        self.assertIn(('status_description', 'Newly created'), data)
        self.assertIn(('is_steady', True), data)
        self.assertIn(('is_healthy', True), data)
        # Created/modified date:
        self.assertIn('created', response.data)
        self.assertIn('modified', response.data)
        # Other details:
        instance_id = app_server.instance.ref.pk
        self.assertIn(
            ('instance', {'id': instance_id, 'api_url': 'http://testserver/api/v1/instance/{}/'.format(instance_id)}),
            data
        )
        self.assertIn('server', response.data)
        server_data = response.data['server'].items()
        self.assertIn(('id', app_server.server.pk), server_data)
        self.assertIn(('public_ip', None), server_data)
        # The API call will try to start the server, which will fail, since we're
        # not actually talking to an OpenStack instance when unit tests are running
        self.assertIn(('status', 'failed'), server_data)
        self.assertIn('log_entries', response.data)
        self.assertIn('log_error_entries', response.data)

    def test_view_name(self):
        """
        Test the verbose name set by get_view_name(), which appears when the API is accessed
        in a web browser.
        """
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/openedx_appserver/', HTTP_ACCEPT="text/html")
        self.assertIn("Open edX App Server List", str(response.content))

        app_server_id = make_test_appserver().pk
        response = self.api_client.get(
            '/api/v1/openedx_appserver/{pk}/'.format(pk=app_server_id), HTTP_ACCEPT="text/html"
        )
        self.assertIn("Open edX App Server Details", str(response.content))

    @patch('instance.models.openedx_instance.OpenEdXAppServer.provision', return_value=True)
    def test_spawn_appserver(self, mock_provision):
        """
        POST /api/v1/openedx_appserver/ - Spawn a new OpenEdXAppServer for the given instance.

        This can be done at any time; there are no restrictions on when a new AppServer can be
        spawned.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40, use_ephemeral_databases=True)
        self.assertEqual(instance.appserver_set.count(), 0)
        self.assertEqual(instance.active_appserver, None)

        response = self.api_client.post('/api/v1/openedx_appserver/', {'instance_id': instance.ref.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'Instance provisioning started'})
        self.assertEqual(mock_provision.call_count, 1)
        instance.refresh_from_db()

        self.assertEqual(instance.appserver_set.count(), 1)
        # Even though provisioning succeeded, the API does not make app servers active automatically:
        self.assertEqual(instance.active_appserver, None)

        app_server = instance.appserver_set.first()
        self.assertEqual(app_server.edx_platform_commit, '1' * 40)

    @patch('instance.models.openedx_instance.gandi.set_dns_record')
    def test_make_active(self, mock_set_dns_record):
        """
        POST /api/v1/openedx_appserver/:id/make_active/ - Make this OpenEdXAppServer active
        for its given instance.

        This can be done at any time; the AppServer must be healthy but "New",
        "WaitingForServer", etc. are all considered healthy states, so the AppServer does not
        necessarily have to be fully provisioned and online.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40, use_ephemeral_databases=True)
        app_server = make_test_appserver(instance)
        self.assertEqual(instance.active_appserver, None)

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_active/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'App server updated.'})
        self.assertEqual(mock_set_dns_record.call_count, 3)  # 3 calls: 1 for LMS, 1 for LMS preview, 1 for Studio

        instance.refresh_from_db()
        self.assertEqual(instance.active_appserver, app_server)

    def test_get_log_entries(self):
        """
        GET - Log entries
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(name="Log Tester Instance")
        app_server = make_test_appserver(instance)
        server = app_server.server
        app_server.logger.info("info")
        app_server.logger.error("error")
        server.logger.info("info")
        server.logger.error("error")

        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_list = [
            {
                'level': 'INFO',
                'text': (
                    'instance.models.appserver | '
                    'instance={inst_id} (Log Tester Inst),app_server={as_id} (AppServer 1) | info'
                ),
            },
            {
                'level': 'ERROR',
                'text': (
                    'instance.models.appserver | '
                    'instance={inst_id} (Log Tester Inst),app_server={as_id} (AppServer 1) | error'
                ),
            },
            {
                'level': 'INFO',
                'text': 'instance.models.server    | server={server_name} | info',
            },
            {
                'level': 'ERROR',
                'text': 'instance.models.server    | server={server_name} | error',
            },
            {
                'level': 'INFO',
                'text': 'instance.models.server    | server={server_name} |'
                        ' Starting server (status=Pending [pending])...'
            },
            {
                'level': 'ERROR',
                'text': 'instance.models.server    | server={server_name} |'
                        ' Failed to start server: Not found (HTTP 404)'
            },
        ]
        self.check_log_list(
            expected_list, response.data['log_entries'],
            inst_id=instance.ref.id, as_id=app_server.pk, server_name=server.name,
        )

    def check_log_list(self, expected_list, log_list, **kwargs):
        """
        Check that the log entries in log_list match expected_list.

        Any kwargs passed will be used to format placeholders in the expected text.
        """
        self.assertEqual(len(expected_list), len(log_list))
        for expected_entry, log_entry in zip(expected_list, log_list):
            self.assertEqual(expected_entry['level'], log_entry['level'])
            text = expected_entry['text'].format(**kwargs)
            self.assertEqual(text, log_entry['text'])

    def test_get_log_error_entries(self):
        """
        GET - Log error entries
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(name="Log Tester Instance")
        app_server = make_test_appserver(instance)
        server = app_server.server
        app_server.logger.info("info")
        app_server.logger.error("error")
        server.logger.info("info")
        server.logger.error("error")

        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_list = [
            {
                'level': 'ERROR',
                'text': (
                    'instance.models.appserver | '
                    'instance={inst_id} (Log Tester Inst),app_server={as_id} (AppServer 1) | error'
                ),
            },
            {
                'level': 'ERROR',
                'text': 'instance.models.server    | server={server_name} | error',
            },
            {
                'level': 'ERROR',
                'text': 'instance.models.server    | server={server_name} |'
                        ' Failed to start server: Not found (HTTP 404)'
            },
        ]
        self.check_log_list(
            expected_list, response.data['log_error_entries'],
            inst_id=instance.ref.id, as_id=app_server.pk, server_name=server.name,
        )
