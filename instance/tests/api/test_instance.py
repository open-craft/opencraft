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
from rest_framework import status

from instance.tests.api.base import APITestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory


# Tests #######################################################################

@ddt.ddt
class InstanceAPITestCase(APITestCase):
    """
    Test cases for Instance API calls

    This only checks the data related to InstanceReference
    (i.e. ID, name, created, modified, and instance_type)
    """
    def test_get_unauthenticated(self):
        """
        GET - Require to be authenticated
        """
        response = self.api_client.get('/api/v1/instance/')
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
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "You do not have permission to perform this action."})

    def test_get_authenticated(self):
        """
        GET - Authenticated - instance manager users allowed access
        """
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        instance = OpenEdXInstanceFactory()
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_serialized_instance(response.data[0], instance)

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
        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': message})

    def check_serialized_instance(self, data, instance):
        """
        Assert that the instance data is what we expect
        """
        self.assertEqual(data['id'], instance.ref.pk)
        self.assertEqual(data['api_url'], 'http://testserver/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(data['name'], instance.name)
        self.assertIn('created', data)
        self.assertIn('modified', data)
        self.assertEqual(data['instance_type'], 'openedxinstance')

    def test_get_details(self):
        """
        GET - Detailed attributes
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_serialized_instance(response.data, instance)

    def test_get_log_entries(self):
        """
        GET - Log entries
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(name="Test!")
        instance.logger.info("info")
        instance.logger.error("error")

        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_list = [
            {'level': 'INFO', 'text': 'instance.models.instance  | instance={inst_id} (Test!) | info'},
            {'level': 'ERROR', 'text': 'instance.models.instance  | instance={inst_id} (Test!) | error'},
        ]
        self.assertEqual(len(expected_list), len(response.data['log_entries']))

        for expected_entry, log_entry in zip(expected_list, response.data['log_entries']):
            self.assertEqual(expected_entry['level'], log_entry['level'])
            self.assertEqual(expected_entry['text'].format(inst_id=instance.ref.pk), log_entry['text'])
