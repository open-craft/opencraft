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
Views - Tests
"""

# Imports #####################################################################

from unittest.mock import patch

import ddt
from rest_framework import status
from django.conf import settings
from instance.tasks import spawn_appserver

from instance.tests.api.base import APITestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.server import ReadyOpenStackServerFactory
from instance.tests.utils import patch_gandi, patch_url


# Tests #######################################################################

@ddt.ddt
class OpenEdXAppServerAPIAcessTestCase(APITestCase):
    """
    Test cases for OpenEdXAppServer API calls related to getting server information.
    """
    def test_get_unauthenticated(self):
        """
        GET - Require to be authenticated
        """
        response = self.api_client.get('/api/v1/openedx_appserver/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    @ddt.data('user1', 'user2')
    def test_get_permission_denied(self, username):
        """
        GET - basic and staff users denied access
        """
        self.api_client.login(username=username, password='pass')
        response = self.api_client.get('/api/v1/openedx_appserver/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "You do not have permission to perform this action."})

    @ddt.data('user3', 'user4')
    def test_get_authenticated(self, username):
        """
        GET - Authenticated - instance manager users (superuser or not) allowed access
        """
        self.api_client.login(username=username, password='pass')
        response = self.api_client.get('/api/v1/openedx_appserver/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        # user4 is instance manager but not superuser
        # Both user3 and user4 should be able to see user4's instance and server in the same way
        instance = OpenEdXInstanceFactory()
        instance.ref.creator = self.user4.profile
        instance.ref.owner = self.user4.profile.organization
        instance.save()
        app_server = make_test_appserver(instance=instance)

        response = self.api_client.get('/api/v1/openedx_appserver/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data[0]
        data_entries = data.items()
        self.assertIn(('id', app_server.pk), data_entries)
        self.assertIn(
            ('api_url', 'http://testserver/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk)),
            data_entries
        )
        self.assertIn(('name', 'AppServer 1'), data_entries)
        # Status fields:
        self.assertIn(('status', 'new'), data_entries)
        self.assertIn(('status_name', 'New'), data_entries)
        self.assertIn(('status_description', 'Newly created'), data_entries)
        self.assertIn(('is_steady', True), data_entries)
        self.assertIn(('is_healthy', True), data_entries)
        # Created/modified/terminated date:
        self.assertIn('created', data)
        self.assertIn('modified', data)
        self.assertIn('terminated', data)
        # Other details should not be in the list view:
        self.assertNotIn('instance', data)
        self.assertNotIn('server', data)
        self.assertNotIn('configuration_settings', data)
        self.assertNotIn('edx_platform_commit', data)
        self.assertNotIn('log_entries', data)
        self.assertNotIn('log_error_entries', data)

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

    @patch_url(settings.OPENSTACK_AUTH_URL)
    @ddt.data('user3', 'user4')
    def test_get_details(self, username):
        """
        GET - Detailed attributes - instance manager (superuser or not) allowed access
        """
        self.api_client.login(username=username, password='pass')
        app_server = make_test_appserver()
        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        data_entries = data.items()
        self.assertIn(('id', app_server.pk), data_entries)
        self.assertIn(
            ('api_url', 'http://testserver/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk)),
            data_entries
        )
        self.assertIn(('name', 'AppServer 1'), data_entries)
        # Status fields:
        self.assertIn(('status', 'new'), data_entries)
        self.assertIn(('status_name', 'New'), data_entries)
        self.assertIn(('status_description', 'Newly created'), data_entries)
        self.assertIn(('is_steady', True), data_entries)
        self.assertIn(('is_healthy', True), data_entries)
        # Created/modified/terminated date:
        self.assertIn('created', data)
        self.assertIn('modified', data)
        self.assertIn('terminated', data)
        # Other details:
        instance_id = app_server.instance.ref.pk
        self.assertIn(
            ('instance', {'id': instance_id, 'api_url': 'http://testserver/api/v1/instance/{}/'.format(instance_id)}),
            data_entries
        )
        self.assertIn('server', data)
        server_data = response.data['server'].items()
        self.assertIn(('id', app_server.server.pk), server_data)
        self.assertIn(('public_ip', None), server_data)
        # The API call will try to start the server, which will fail, since we're
        # not actually talking to an OpenStack instance when unit tests are running
        self.assertIn(('status', 'failed'), server_data)
        self.assertIn('log_entries', data)
        self.assertIn('log_error_entries', data)

    def test_get_servers_from_different_org(self):
        """
        GET - A non-superuser instance manager from organization 1 can't find servers from organization 2
        (that is, servers belonging to instances owned by organization 2).
        """
        self.api_client.login(username='user4', password='pass')

        # Instance 1 belongs to user4's organization (which is organization2)
        instance1 = OpenEdXInstanceFactory()
        instance1.ref.creator = self.user4.profile
        instance1.ref.owner = self.organization2
        instance1.save()
        app_server_i1 = make_test_appserver(instance=instance1)

        # Instance 2 doesn't belong to user4's organization (organization2). It was created by another user (user1)
        instance2 = OpenEdXInstanceFactory()
        instance2.ref.creator = self.user1.profile
        instance2.ref.owner = self.organization
        instance2.save()
        app_server_i2 = make_test_appserver(instance=instance2)

        # Only the first server should be listed
        response = self.api_client.get('/api/v1/openedx_appserver/')
        data_entries = response.data[0].items()
        self.assertIn(('id', app_server_i1.pk), data_entries)
        self.assertNotIn(('id', app_server_i2.pk), data_entries)

        # Only the first server should be directly accessible
        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/'.format(pk=app_server_i1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/'.format(pk=app_server_i2.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@ddt.ddt
class OpenEdXAppServerAPISpawnServerTestCase(APITestCase):
    """
    Test cases for OpenEdXAppServer API calls related to spawning new servers.
    """

    @patch_gandi
    @patch('instance.models.openedx_instance.OpenEdXInstance.provision_rabbitmq')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    @patch('instance.models.mixins.load_balanced.LoadBalancingServer.run_playbook')
    def test_spawn_appserver(self, mock_run_playbook, mock_provision, mock_provision_rabbitmq):
        """
        POST /api/v1/openedx_appserver/ - Spawn a new OpenEdXAppServer for the given instance.

        This can be done at any time; there are no restrictions on when a new AppServer can be
        spawned.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        self.assertEqual(instance.appserver_set.count(), 0)
        self.assertFalse(instance.get_active_appservers().exists())

        response = self.api_client.post('/api/v1/openedx_appserver/', {'instance_id': instance.ref.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'Instance provisioning started'})
        self.assertEqual(mock_provision.call_count, 1)
        self.assertEqual(mock_provision_rabbitmq.call_count, 1)
        instance.refresh_from_db()

        self.assertEqual(instance.appserver_set.count(), 1)
        # Even though provisioning succeeded, the API does not make app servers active automatically:
        self.assertFalse(instance.get_active_appservers().exists())

        app_server = instance.appserver_set.first()
        self.assertEqual(app_server.edx_platform_commit, '1' * 40)

    @ddt.data(True, False)
    @patch_gandi
    @patch('instance.models.openedx_instance.OpenEdXInstance.provision_rabbitmq')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    @patch('instance.models.mixins.load_balanced.LoadBalancingServer.run_playbook')
    def test_spawn_appserver_break_on_success(self, mark_active, mock_run_playbook, mock_provision,
                                              mock_provision_rabbitmq):
        """
        This test makes sure that upon a successful instance creation, further instances are not created
        even when the num_attempts is more than 1.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        self.assertEqual(instance.appserver_set.count(), 0)
        self.assertFalse(instance.get_active_appservers().exists())

        spawn_appserver(instance.ref.pk, mark_active_on_success=mark_active, num_attempts=4)
        self.assertEqual(mock_provision.call_count, 1)
        self.assertEqual(mock_provision_rabbitmq.call_count, 1)

    @ddt.data(
        (None, 'Authentication credentials were not provided.'),
        ('user1', 'You do not have permission to perform this action.'),
        ('user2', 'You do not have permission to perform this action.'),
    )
    @ddt.unpack
    def test_spawn_appserver_denied(self, username, message):
        """
        POST - Anonymous, basic, and staff users (without manage_own permission) can't spawn servers.
        """
        if username:
            self.api_client.login(username=username, password='pass')
        instance = OpenEdXInstanceFactory()
        response = self.api_client.post('/api/v1/openedx_appserver/', {'instance_id': instance.ref.pk})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': message})

    def test_spawn_appserver_no_organization(self):
        """
        POST - An instance manager user without an organization can't spawn servers
        (because they can't see any instance either).
        """
        self.api_client.login(username='user5', password='pass')
        instance = OpenEdXInstanceFactory()
        response = self.api_client.post('/api/v1/openedx_appserver/', {'instance_id': instance.ref.pk})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_spawn_appserver_different_org(self):
        """
        POST - An instance manager can't spawn a server in an organization they don't belong to.
        """
        self.api_client.login(username='user4', password='pass')
        # This instance does not belong to user4's organization (organization2)
        instance = OpenEdXInstanceFactory()
        instance.ref.creator = self.user1.profile
        instance.ref.owner = self.organization
        instance.save()

        response = self.api_client.post('/api/v1/openedx_appserver/', {'instance_id': instance.ref.pk})
        # Not found (instead of: forbidden), because this server was never visible to user4
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(instance.appserver_set.count(), 0)


@ddt.ddt
class OpenEdXAppServerAPIMakeActiveTestCase(APITestCase):
    """
    Test cases for OpenEdXAppServer API calls related to activation/deactivation of servers.
    """

    @patch_gandi
    @patch('instance.models.server.OpenStackServer.public_ip')
    @patch('instance.models.load_balancer.LoadBalancingServer.run_playbook')
    def test_make_active(self, mock_run_playbook, mock_public_ip):
        """
        POST /api/v1/openedx_appserver/:id/make_active/ - Make this OpenEdXAppServer active
        for its given instance.

        This can be done at any time; the AppServer must be healthy but "New",
        "WaitingForServer", etc. are all considered healthy states, so the AppServer does not
        necessarily have to be fully provisioned and online.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        server = ReadyOpenStackServerFactory()
        app_server = make_test_appserver(instance=instance, server=server)
        self.assertFalse(instance.get_active_appservers().exists())

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_active/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'App server activation initiated.'})
        self.assertEqual(mock_run_playbook.call_count, 1)

        instance.refresh_from_db()
        self.assertEqual(list(instance.get_active_appservers().all()), [app_server])
        app_server.refresh_from_db()
        self.assertTrue(app_server.is_active)

    @patch('instance.models.load_balancer.LoadBalancingServer.run_playbook')
    def test_make_active_unhealthy(self, mock_run_playbook):
        """
        POST /api/v1/openedx_appserver/:id/make_active/ - AppServer must be healthy
        to be activated
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        app_server = make_test_appserver(instance)

        # Move to unhealthy status
        app_server._status_to_waiting_for_server()
        app_server._status_to_error()

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_active/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Cannot make an unhealthy app server active.'})
        self.assertEqual(mock_run_playbook.call_count, 0)

    @patch_gandi
    @patch('instance.models.server.OpenStackServer.public_ip')
    @patch('instance.models.load_balancer.LoadBalancingServer.run_playbook')
    def test_make_inactive(self, mock_run_playbook, mock_public_ip):
        """
        POST /api/v1/openedx_appserver/:id/make_inactive/ - Make this OpenEdXAppServer inactive
        for its given instance.

        AppServer does not need to be healty to be deactivated.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        server = ReadyOpenStackServerFactory()
        app_server = make_test_appserver(instance=instance, server=server)
        self.assertFalse(instance.get_active_appservers().exists())

        # Make the server active
        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_active/'.format(pk=app_server.pk))
        instance.refresh_from_db()
        self.assertEqual(list(instance.get_active_appservers().all()), [app_server])
        app_server.refresh_from_db()
        self.assertTrue(app_server.is_active)

        # Make the server inactive
        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_inactive/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'App server deactivation initiated.'})
        self.assertEqual(mock_run_playbook.call_count, 2)

        instance.refresh_from_db()
        self.assertFalse(instance.get_active_appservers().exists())
        app_server.refresh_from_db()
        self.assertFalse(app_server.is_active)

    @patch_gandi
    @patch('instance.models.server.OpenStackServer.public_ip')
    @patch('instance.models.load_balancer.LoadBalancingServer.run_playbook')
    def test_make_inactive_unhealthy(self, mock_run_playbook, mock_public_ip):
        """
        POST /api/v1/openedx_appserver/:id/make_inactive/ - unheahtly AppServers can be deactivated
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        server = ReadyOpenStackServerFactory()
        app_server = make_test_appserver(instance=instance, server=server)
        self.assertFalse(instance.get_active_appservers().exists())

        # Make the server active
        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_active/'.format(pk=app_server.pk))
        instance.refresh_from_db()
        self.assertEqual(list(instance.get_active_appservers().all()), [app_server])
        app_server.refresh_from_db()
        self.assertTrue(app_server.is_active)

        # Move to unhealthy status
        app_server._status_to_waiting_for_server()
        app_server._status_to_error()

        # Make the server inactive
        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_inactive/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'App server deactivation initiated.'})
        self.assertEqual(mock_run_playbook.call_count, 2)

        instance.refresh_from_db()
        self.assertFalse(instance.get_active_appservers().exists())
        app_server.refresh_from_db()
        self.assertFalse(app_server.is_active)

    @ddt.data(
        (None, 'Authentication credentials were not provided.'),
        ('user1', 'You do not have permission to perform this action.'),
        ('user2', 'You do not have permission to perform this action.'),
    )
    @ddt.unpack
    def test_make_active_permission_denied(self, username, message):
        """
        POST - Anonymous, basic, and staff users (without manage_own permission) can't make servers active/inactive.
        """
        if username:
            self.api_client.login(username=username, password='pass')

        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        server = ReadyOpenStackServerFactory()
        app_server = make_test_appserver(instance=instance, server=server)

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_active/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': message})

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_inactive/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': message})

    def test_make_active_no_organization(self):
        """
        POST - An instance manager user without an organization can't activate/deactivate servers
        (since they don't belong to the user's organization, because there isn't one).
        """
        self.api_client.login(username='user5', password='pass')

        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        server = ReadyOpenStackServerFactory()
        app_server = make_test_appserver(instance=instance, server=server)

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_active/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_inactive/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_make_active_different_org(self):
        """
        POST - An instance manager can't activate/deactive a server in an organization they don't belong to.
        """
        self.api_client.login(username='user4', password='pass')

        # user4 won't be able to access this instance because it belongs to user1's organization
        instance = OpenEdXInstanceFactory()
        instance.ref.creator = self.user1.profile
        instance.ref.owner = self.user1.profile.organization
        instance.save()
        server = ReadyOpenStackServerFactory()
        app_server = make_test_appserver(instance=instance, server=server)

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_active/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/make_inactive/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OpenEdXAppServerAPITerminate(APITestCase):
    """
    Test cases for OpenEdXAppServer API calls related to termination of servers.
    """

    def setUp(self):
        super().setUp()
        self.api_client.login(username='user3', password='pass')

    def _create_appserver(self, is_active):
        """
        Creates test instance and app server
        """
        instance = OpenEdXInstanceFactory(edx_platform_commit='1' * 40)
        server = ReadyOpenStackServerFactory()
        app_server = make_test_appserver(instance=instance, server=server)
        self.assertFalse(instance.get_active_appservers().exists())

        app_server.make_active(is_active)
        self.assertEqual(app_server.is_active, is_active)
        return instance, app_server

    @patch_gandi
    @patch('instance.models.server.OpenStackServer.public_ip')
    @patch('instance.models.load_balancer.LoadBalancingServer.run_playbook')
    @patch('instance.models.server.OpenStackServer.terminate')
    def test_terminate_inactive(self, mock_terminate_server, mock_run_playbook, mock_public_ip):
        """
        POST /api/v1/openedx_appserver/:id/terminate/ - Terminate this OpenEdXAppServer VM.

        Inactive app servers are terminated.
        """
        instance, app_server = self._create_appserver(False)
        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/terminate/'.format(pk=app_server.pk))
        instance.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'App server termination initiated.'})
        self.assertEqual(mock_terminate_server.call_count, 1)

    @patch_gandi
    @patch('instance.models.server.OpenStackServer.public_ip')
    @patch('instance.models.load_balancer.LoadBalancingServer.run_playbook')
    @patch('instance.models.server.OpenStackServer.terminate')
    def test_terminate_active(self, mock_terminate_server, mock_run_playbook, mock_public_ip):
        """
        POST /api/v1/openedx_appserver/:id/terminate/ - Terminate this OpenEdXAppServer VM.

        AppServer must be deactivated to be terminated.
        """
        instance, app_server = self._create_appserver(True)
        response = self.api_client.post('/api/v1/openedx_appserver/{pk}/terminate/'.format(pk=app_server.pk))
        instance.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Cannot terminate an active app server.'})
        self.assertEqual(mock_terminate_server.call_count, 0)


@ddt.ddt
class OpenEdXAppServerAPILogsTestCase(APITestCase):
    """
    Test cases for OpenEdXAppServer API calls related to logs
    """

    @patch_url(settings.OPENSTACK_AUTH_URL)
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
                'text': 'instance.models.server    | server={server_id} ({server_name}) | info',
            },
            {
                'level': 'ERROR',
                'text': 'instance.models.server    | server={server_id} ({server_name}) | error',
            },
            {
                'level': 'INFO',
                'text': 'instance.models.server    | server={server_id} ({server_name}) |'
                        ' Starting server (status=Pending [pending])...'
            },
            {
                'level': 'ERROR',
                'text': 'instance.models.server    | server={server_id} ({server_name}) |'
                        ' Failed to start server: Not found (HTTP 404)'
            },
            {
                'level': 'INFO',
                'text': 'instance.models.server    | server={server_id} ({server_name}) |'
                        ' Transition from "Pending" to "Failed"'
            },
        ]
        self.check_log_list(
            expected_list, response.data['log_entries'],
            inst_id=instance.ref.id, as_id=app_server.pk, server_id=server.pk, server_name=server.name,
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

    @patch_url(settings.OPENSTACK_AUTH_URL)
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
                'text': 'instance.models.server    | server={server_id} ({server_name}) |'
                        ' Failed to start server: Not found (HTTP 404)'
            },
            {
                'level': 'INFO',
                'text': 'instance.models.server    | server={server_id} ({server_name}) |'
                        ' Transition from "Pending" to "Failed"'
            },
        ]

        self.check_log_list(
            expected_list, response.data['log_error_entries'],
            inst_id=instance.ref.id, as_id=app_server.pk, server_id=server.pk, server_name=server.name,
        )

    @ddt.data(
        (None, 'Authentication credentials were not provided.'),
        ('user1', 'You do not have permission to perform this action.'),
        ('user2', 'You do not have permission to perform this action.'),
    )
    @ddt.unpack
    def test_get_logs_permission_denied(self, username, message):
        """
        GET - Basic users and anonymous can't get an appserver's log entries.
        """
        if username:
            self.api_client.login(username=username, password='pass')
        instance = OpenEdXInstanceFactory()
        app_server = make_test_appserver(instance)
        server = app_server.server
        app_server.logger.info("info")
        server.logger.info("info")
        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/logs/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': message})

    def test_get_logs_different_organization(self):
        """
        GET - An instance manager can't get appserver logs if the instance belongs to a different organization.
        """
        self.api_client.login(username='user4', password='pass')
        instance = OpenEdXInstanceFactory()
        instance.ref.creator = self.user1.profile
        instance.ref.owner = self.user1.profile.organization
        instance.save()
        app_server = make_test_appserver(instance)
        server = app_server.server
        app_server.logger.info("info")
        server.logger.info("info")
        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/logs/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_logs_no_organization(self):
        """
        GET - An instance manager without an organization can't get logs of any appserver.
        """
        self.api_client.login(username='user5', password='pass')
        instance = OpenEdXInstanceFactory()
        app_server = make_test_appserver(instance)
        server = app_server.server
        app_server.logger.info("info")
        server.logger.info("info")
        response = self.api_client.get('/api/v1/openedx_appserver/{pk}/logs/'.format(pk=app_server.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
