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
Views - Tests
"""

# Imports #####################################################################

from mock import patch

from rest_framework import status

from instance.tests.api.base import APITestCase
from instance.tests.models.factories.instance import OpenEdXInstanceFactory
from instance.tests.models.factories.server import OpenStackServerFactory


# Tests #######################################################################

class InstanceAPITestCase(APITestCase):
    """
    Test cases for Instance API calls
    """
    # To avoid errors with `response.data` from REST framework's API client
    #pylint: disable=no-member

    def test_get_unauthenticated(self):
        """
        GET - Require to be authenticated
        """
        response = self.api_client.get('/api/v1/openedxinstance/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_get_authenticated(self):
        """
        GET - Authenticated
        """
        self.api_client.login(username='user1', password='pass')
        response = self.api_client.get('/api/v1/openedxinstance/')
        self.assertEqual(response.data, [])

        instance = OpenEdXInstanceFactory()
        response = self.api_client.get('/api/v1/openedxinstance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(('id', instance.pk), response.data[0].items())
        self.assertIn(('api_url', 'http://testserver/api/v1/openedxinstance/{pk}/'.format(pk=instance.pk)),
                      response.data[0].items())
        self.assertIn(('status', 'empty'), response.data[0].items())
        self.assertIn(('base_domain', 'example.com'), response.data[0].items())

    def test_provision_not_ready(self):
        """
        POST /:id/provision - Status not ready
        """
        self.api_client.login(username='user1', password='pass')
        instance = OpenEdXInstanceFactory()
        OpenStackServerFactory(instance=instance)
        response = self.api_client.post('/api/v1/openedxinstance/{pk}/provision/'.format(pk=instance.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('instance.api.instance.provision_instance')
    def test_provision(self, mock_provision_instance):
        """
        POST /:id/provision
        """
        self.api_client.login(username='user1', password='pass')
        instance = OpenEdXInstanceFactory()
        OpenStackServerFactory(instance=instance, status='ready')
        response = self.api_client.post('/api/v1/openedxinstance/{pk}/provision/'.format(pk=instance.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'Instance provisioning started'})
        self.assertEqual(mock_provision_instance.call_count, 1)
