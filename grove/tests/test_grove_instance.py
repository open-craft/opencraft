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

from rest_framework import status

from django.conf import settings
from django.test.utils import override_settings
from grove.tests.base import APITestCase
from grove.tests.models.factories.grove_instance import GroveInstanceFactory


# Tests #######################################################################

class GroveInstanceAPITestCase(APITestCase):
    """
    Test cases for Instance API calls. Checks data that is specific to GroveInstance
    """
    def check_serialized_instance(self, data, instance):
        """
        Assert that the instance data is what we expect
        """
        self.assertEqual(data['id'], instance.ref.pk)
        self.assertEqual(data['api_url'], 'http://testserver/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(data['name'], instance.name)
        self.assertIn('created', data)
        self.assertIn('modified', data)
        self.assertEqual(data['instance_type'], 'groveinstance')

    @override_settings(USE_GROVE_INSTANCE=True)
    def test_list_grove_instances(self):
        """
        GET - List of Grove instances
        """
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        instance_1 = GroveInstanceFactory(
            internal_lms_domain='sample.example.org',
            edx_platform_commit=settings.DEFAULT_OPENEDX_RELEASE
        )
        # create one more instance
        GroveInstanceFactory(
            internal_lms_domain='test.example.org',
            edx_platform_commit=settings.DEFAULT_OPENEDX_RELEASE
        )
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.check_serialized_instance(response.data[1], instance_1)

    @override_settings(USE_GROVE_INSTANCE=True)
    def test_get_grove_instance(self):
        """
        Get - Retrieve grove instance details
        """
        self.api_client.login(username='user3', password='pass')
        instance = GroveInstanceFactory(
            internal_lms_domain='sample.example.org',
            edx_platform_commit=settings.DEFAULT_OPENEDX_RELEASE
        )
        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_serialized_instance(response.data, instance)
