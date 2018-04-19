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

import ddt
from django.conf import settings
from rest_framework import status

from instance.tests.api.base import APITestCase
from instance.tests.models.factories.server import OpenStackServerFactory


# Tests #######################################################################

@ddt.ddt
class OpenStackServerAPITestCase(APITestCase):
    """
    Test cases for OpenStackServer API calls
    """

    def test_get_unauthenticated(self):
        """
        GET - Require to be authenticated
        """
        response = self.api_client.get('/api/v1/openstackserver/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    def test_get_authenticated(self):
        """
        GET - Authenticated access
        """
        self.api_client.login(username='user1', password='pass')
        response = self.api_client.get('/api/v1/openstackserver/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        server = OpenStackServerFactory()
        response = self.api_client.get('/api/v1/openstackserver/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_serialized_server(response.data[0], server)

    def test_get_details(self):
        """
        GET - Detailed attributes
        """
        self.api_client.login(username='user3', password='pass')

        test_openstack_id = 'test-openstack-id'
        server = OpenStackServerFactory(openstack_id=test_openstack_id)
        response = self.api_client.get('/api/v1/openstackserver/{pk}/'.format(pk=server.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_serialized_server(response.data, server)
        self.assertEqual(response.data['openstack_id'], test_openstack_id)

    def check_serialized_server(self, data, server):
        """
        Assert that the server data is what we expect
        """
        self.assertEqual(data['id'], server.id)
        self.assertEqual(
            data['api_url'],
            'http://testserver/api/v1/openstackserver/{pk}/'.format(pk=server.id)
        )
        self.assertEqual(data['name'], server.name)
        self.assertEqual(data['openstack_region'], settings.OPENSTACK_REGION)
        self.assertIn('created', data)
        self.assertIn('modified', data)
        self.assertIn('openstack_id', data)
        self.assertIn('public_ip', data)
        self.assertIn('status', data)
