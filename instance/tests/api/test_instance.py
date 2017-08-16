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

from django.conf import settings
from django.test.utils import override_settings
from instance.tests.api.base import APITestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
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

    def test_list_archived_instances(self):
        """
        GET - List of instances should exclude archived instances
        by default, but show them if explicitly requested.
        """
        self.api_client.login(username='user3', password='pass')
        regular_instance = OpenEdXInstanceFactory()
        archived_instance = OpenEdXInstanceFactory()
        archived_instance.ref.is_archived = True
        archived_instance.ref.save()

        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.check_serialized_instance(response.data[0], regular_instance)

        response = self.api_client.get('/api/v1/instance/?include_archived')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Newer instances are first, so the archived instance will be first:
        self.check_serialized_instance(response.data[0], archived_instance)
        self.check_serialized_instance(response.data[1], regular_instance)

        # Verify that no App Servers are returned when querying the instance list
        for data in (response.data[0], response.data[1]):
            self.assertTrue(('appservers' not in data), "There should be no app servers for instance in list")

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

    def test_not_all_appservers_are_loaded_by_default(self):
        """
        Tries to add e.g. 7 appservers and then verifies that only 5 are returned initially.
        That is, the results are filtered by the NUM_INITIAL_APPSERVERS_SHOWN setting.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        for _ in range(settings.NUM_INITIAL_APPSERVERS_SHOWN + 2):
            make_test_appserver(instance)

        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # After creating e.g. 7, we check that 7 exist but only 5 are loaded
        self.assertEqual(response.data['appserver_count'], settings.NUM_INITIAL_APPSERVERS_SHOWN + 2)
        self.assertTrue(
            len(response.data['appservers']) <= settings.NUM_INITIAL_APPSERVERS_SHOWN,
            "Too many initial app servers for instance detail"
        )

    def test_get_log_entries(self):
        """
        GET - Log entries
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(name="Test!")
        instance.logger.info("info")
        instance.logger.error("error")

        response = self.api_client.get('/api/v1/instance/{pk}/logs/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_list = [
            {'level': 'INFO', 'text': 'instance.models.instance  | instance={inst_id} (Test!) | info'},
            {'level': 'ERROR', 'text': 'instance.models.instance  | instance={inst_id} (Test!) | error'},
        ]
        log_entries = response.data['log_entries']
        self.assertEqual(len(expected_list), len(log_entries))

        for expected_entry, log_entry in zip(expected_list, log_entries):
            self.assertEqual(expected_entry['level'], log_entry['level'])
            self.assertEqual(expected_entry['text'].format(inst_id=instance.ref.pk), log_entry['text'])
            self.assertEqual(expected_entry['text'].format(inst_id=instance.ref.pk), log_entry['text'])

    @override_settings(NUM_INITIAL_APPSERVERS_SHOWN=5)
    def test_get_app_servers_list(self):
        """
        GET - App Servers
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(name="Test!")

        for _ in range(10):
            make_test_appserver(instance)

        response = self.api_client.get('/api/v1/instance/{pk}/app_servers/'.format(pk=instance.ref.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertTrue('app_servers' in response.data)

        # Verify that all of them are returned, not only NUM_INITIAL_APPSERVERS_SHOWN
        self.assertEqual(len(response.data['app_servers']), 10)
        self.assertTrue('name' in response.data['app_servers'][0])
        self.assertTrue('name' in response.data['app_servers'][9])
