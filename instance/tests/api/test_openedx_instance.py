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
    # To avoid errors with `response.data` from REST framework's API client
    #pylint: disable=no-member

    def test_get_authenticated(self):
        """
        GET - Authenticated
        """
        self.api_client.login(username='user1', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.data, [])

        OpenEdXInstanceFactory(sub_domain='domain.api')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance_data = response.data[0].items()
        self.assertIn(('domain', 'domain.api.example.com'), instance_data)
        self.assertIn(('appserver_count', 0), instance_data)
        self.assertIn(('active_appserver', None), instance_data)
        self.assertIn(('newest_appserver', None), instance_data)

    def test_get_details(self):
        """
        GET - Detailed attributes
        """
        self.api_client.login(username='user1', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        app_server = make_test_appserver(instance)
        instance.active_appserver = app_server  # Outside of tests, use set_appserver_active() instead
        instance.save()

        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        instance_data = response.data.items()
        self.assertIn(('domain', 'domain.api.example.com'), instance_data)
        self.assertIn(('name', instance.name), instance_data)
        self.assertIn(('url', 'http://domain.api.example.com/'), instance_data)
        self.assertIn(('studio_url', 'http://studio-domain.api.example.com/'), instance_data)
        self.assertIn(
            ('edx_platform_repository_url', 'https://github.com/{}.git'.format(settings.DEFAULT_FORK)),
            instance_data
        )
        self.assertIn(('edx_platform_commit', 'master'), instance_data)
        # AppServer info:
        self.assertIn(('appserver_count', 1), instance_data)
        self.assertIn('active_appserver', response.data)
        self.assertIn('newest_appserver', response.data)
        for key in ('active_appserver', 'newest_appserver'):
            app_server_data = response.data[key]
            self.assertEqual(app_server_data['id'], app_server.pk)
            self.assertEqual(
                app_server_data['api_url'], 'http://testserver/api/v1/openedx_appserver/{pk}/'.format(pk=app_server.pk)
            )
            self.assertEqual(app_server_data['status'], 'new')

    def test_view_name(self):
        """
        Test the verbose name set by get_view_name(), which appears when the API is accessed
        in a web browser.
        """
        self.api_client.login(username='user1', password='pass')
        response = self.api_client.get('/api/v1/instance/', HTTP_ACCEPT="text/html")
        self.assertIn("Instance List", str(response.content))

        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk), HTTP_ACCEPT="text/html")
        self.assertIn("Instance Details", str(response.content))
