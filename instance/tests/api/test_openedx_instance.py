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

from django.conf import settings
from rest_framework import status

from instance.tests.api.base import APITestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.openedx_appserver import make_test_appserver


# Tests #######################################################################

class OpenEdXInstanceAPITestCase(APITestCase):
    """
    Test cases for Instance API calls. Checks data that is specific to OpenEdXInstance
    """
    def test_get_authenticated(self):
        """
        GET - Authenticated - instance manager user is allowed access
        """
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.data, [])

        OpenEdXInstanceFactory(sub_domain='domain.api')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance_data = response.data[0].items()
        self.assertIn(('domain', 'domain.api.example.com'), instance_data)
        self.assertIn(('is_shut_down', False), instance_data)
        self.assertIn(('appserver_count', 0), instance_data)
        self.assertIn(('active_appservers', []), instance_data)
        self.assertIn(('is_healthy', None), instance_data)
        self.assertIn(('is_steady', None), instance_data)
        self.assertIn(('status_description', ''), instance_data)
        self.assertIn(('newest_appserver', None), instance_data)

    def add_active_appserver(self):
        """
        Create an instance, and add an active appserver.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        app_server = make_test_appserver(instance)
        app_server.is_active = True  # Outside of tests, use app_server.make_active() instead
        app_server.save()
        return instance, app_server

    def assert_active_appserver(self, instance_id, appserver_id):
        """
        Verify the API returns valid instance data with an active appserver.
        """
        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        instance_data = response.data.items()
        self.assertIn(('domain', 'domain.api.example.com'), instance_data)
        self.assertIn(('is_shut_down', False), instance_data)
        self.assertIn(('url', 'https://domain.api.example.com/'), instance_data)
        self.assertIn(('studio_url', 'https://studio-domain.api.example.com/'), instance_data)
        self.assertIn(
            ('edx_platform_repository_url', 'https://github.com/{}.git'.format(settings.DEFAULT_FORK)),
            instance_data
        )
        self.assertIn(('edx_platform_commit', 'master'), instance_data)
        self.assertIn(('additional_security_groups', []), instance_data)

        # AppServer info:
        self.assertIn(('appserver_count', 1), instance_data)
        self.assertIn('active_appservers', response.data)
        self.assertIn('newest_appserver', response.data)
        for app_server_data in response.data['active_appservers'] + [response.data['newest_appserver']]:
            self.assertEqual(app_server_data['id'], appserver_id)
            self.assertEqual(
                app_server_data['api_url'], 'http://testserver/api/v1/openedx_appserver/{pk}/'.format(pk=appserver_id)
            )
        return response

    def test_get_details(self):
        """
        GET - Detailed attributes
        """
        instance, app_server = self.add_active_appserver()

        response = self.assert_active_appserver(instance.ref.id, app_server.pk)
        instance_data = response.data.items()
        self.assertIn(('name', instance.name), instance_data)
        self.assertIn(('is_healthy', True), instance_data)
        self.assertIn(('is_steady', True), instance_data)
        self.assertIn(('status_description', 'Newly created'), instance_data)
        self.assertEqual(response.data['active_appservers'][0]['status'], 'new')

    def test_get_details_unsteady(self):
        """
        GET - Detailed attributes
        """
        # Make app_server unsteady
        instance, app_server = self.add_active_appserver()
        app_server._status_to_waiting_for_server()
        app_server.save()

        response = self.assert_active_appserver(instance.ref.id, app_server.pk)
        instance_data = response.data.items()
        self.assertIn(('name', instance.name), instance_data)
        self.assertIn(('is_healthy', True), instance_data)
        self.assertIn(('is_steady', False), instance_data)
        self.assertIn(('status_description', 'VM not yet accessible'), instance_data)
        self.assertEqual(response.data['active_appservers'][0]['status'], 'waiting')

    def test_get_details_unhealthy(self):
        """
        GET - Detailed attributes
        """
        # Make app_server unhealthy
        instance, app_server = self.add_active_appserver()
        app_server._status_to_waiting_for_server()
        app_server._status_to_error()
        app_server.save()

        response = self.assert_active_appserver(instance.ref.id, app_server.pk)
        instance_data = response.data.items()
        self.assertIn(('name', instance.name), instance_data)
        self.assertIn(('is_healthy', False), instance_data)
        self.assertIn(('is_steady', True), instance_data)
        self.assertIn(('status_description', 'App server never got up and running '
                       '(something went wrong when trying to build new VM)'), instance_data)
        self.assertEqual(response.data['active_appservers'][0]['status'], 'error')
