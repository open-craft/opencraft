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
from django.test.utils import override_settings
from instance.tests.api.base import APITestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory


# Tests #######################################################################

@ddt.ddt
@patch(
    'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class InstanceAPITestCase(APITestCase):
    """
    Test cases for Instance API calls

    This only checks the data related to InstanceReference
    (i.e. ID, name, created, modified, and instance_type)
    """
    def test_get_unauthenticated(self, mock_consul):
        """
        GET - Require to be authenticated
        """
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    @ddt.data('user1', 'user2')
    def test_get_permission_denied(self, username, mock_consul):
        """
        GET - basic and staff users denied access
        """
        self.api_client.login(username=username, password='pass')
        OpenEdXInstanceFactory()
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "You do not have permission to perform this action."})

    def test_get_authenticated(self, mock_consul):
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

    def test_list_archived_instances(self, mock_consul):
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
    def test_get_details_permission_denied(self, username, message, mock_consul):
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

    def test_get_details(self, mock_consul):
        """
        GET - Detailed attributes for staff and superuser user

        Staff and Superuser user is able to see instance notes.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_serialized_instance(response.data, instance)
        self.assertIn('notes', response.data)

    def test_get_details_does_not_have_notes_if_no_staff_and_no_superuser(self, mock_consul):
        """
        GET - Detailed attributes for owner user

        User can see instance from the same organization, but instance notes is not in response.
        """
        self.api_client.login(username='user4', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        instance.ref.owner = self.user4.profile.organization
        instance.ref.save()
        response = self.api_client.get('/api/v1/instance/{pk}/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.check_serialized_instance(response.data, instance)
        self.assertNotIn('notes', response.data)

    def test_not_all_appservers_are_loaded_by_default(self, mock_consul):
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

    def test_get_log_entries(self, mock_consul):
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

    @ddt.data(
        (None, 'Authentication credentials were not provided.'),
        ('user1', 'You do not have permission to perform this action.'),
        ('user2', 'You do not have permission to perform this action.'),
    )
    @ddt.unpack
    def test_get_logs_permission_denied(self, username, message, mock_consul):
        """
        GET - Basic users and anonymous can't get log entries
        """
        if username:
            self.api_client.login(username=username, password='pass')
        instance = OpenEdXInstanceFactory()
        response = self.api_client.get('/api/v1/instance/{pk}/logs/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': message})

    def test_get_logs_different_organization(self, mock_consul):
        """
        GET - An instance manager can't get logs of an instance which belongs to a different organization.
        """
        self.api_client.login(username='user4', password='pass')
        instance = OpenEdXInstanceFactory()
        instance.ref.creator = self.user1.profile
        instance.ref.owner = self.user1.profile.organization
        instance.save()
        response = self.api_client.get('/api/v1/instance/{pk}/logs/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_logs_no_organization(self, mock_consul):
        """
        GET - An instance manager without an organization can't get logs of any instance.
        """
        self.api_client.login(username='user5', password='pass')
        instance = OpenEdXInstanceFactory()
        response = self.api_client.get('/api/v1/instance/{pk}/logs/'.format(pk=instance.ref.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(NUM_INITIAL_APPSERVERS_SHOWN=5)
    def test_get_app_servers_list(self, mock_consul):
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

    def test_set_notes_instance_updates(self, mock_consul):
        """
        POST - Update instance notes
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(name='Test!')

        self.assertEqual(instance.ref.notes, '')

        response = self.api_client.post('/api/v1/instance/{pk}/set_notes/'.format(pk=instance.ref.pk),
                                        {'notes': 'Test notes'})

        instance.ref.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(instance.ref.notes, 'Test notes')

    def test_set_notes_instance_do_nothing_if_notes_not_in_payload(self, mock_consul):
        """
        POST - Update instance notes does not change if not 'notes' field is provided
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(name='Test!')

        self.assertEqual(instance.ref.notes, '')

        old_instance_ref_dict = instance.ref.__dict__.copy()
        response = self.api_client.post('/api/v1/instance/{pk}/set_notes/'.format(pk=instance.ref.pk))
        instance.ref.refresh_from_db()
        current_instance_ref_dict = {}
        for k, _ in old_instance_ref_dict.items():
            current_instance_ref_dict[k] = instance.ref.__dict__[k]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({'status': 'No notes value provided.'}, response.data)
        self.assertEqual(current_instance_ref_dict, old_instance_ref_dict)

    @patch(
        'instance.serializers.instance.InstanceReferenceBasicSerializer.is_valid',
        return_value=False
    )
    def test_set_notes_instance_gives_error_if_extra_field_is_provided(self, mock_consul, mock_is_valid):
        """
        POST - Update instance notes returns 400 if trying to save invalid data
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(name='Test!')

        self.assertFalse(mock_is_valid.called)

        response = self.api_client.post('/api/v1/instance/{pk}/set_notes/'.format(pk=instance.ref.pk),
                                        {'notes': 'Test notes'})

        self.assertFalse(mock_is_valid.called)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual({"error": "Instance attributes are not valid."}, response.data)
