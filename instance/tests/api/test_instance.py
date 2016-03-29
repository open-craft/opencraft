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

from mock import call, patch
from rest_framework import status

from instance import github
from instance.models.instance import OpenEdXInstance
from instance.models.server import OpenStackServer
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

    def test_get_domain(self):
        """
        GET - Domain attributes
        """
        self.api_client.login(username='user1', password='pass')
        OpenEdXInstanceFactory(sub_domain='domain.api')
        response = self.api_client.get('/api/v1/openedxinstance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(('domain', 'domain.api.example.com'), response.data[0].items())
        self.assertIn(('url', 'http://domain.api.example.com/'), response.data[0].items())
        self.assertIn(('studio_url', 'http://studio.domain.api.example.com/'), response.data[0].items())

    def test_provision_not_ready(self):
        """
        POST /:id/provision - Status not ready
        """
        self.api_client.login(username='user1', password='pass')
        instance = OpenEdXInstanceFactory()
        OpenStackServerFactory(instance=instance, progress=OpenStackServer.Progress.Running)
        self.assertEqual(instance.progress, OpenStackServer.Progress.Running)
        response = self.api_client.post('/api/v1/openedxinstance/{pk}/provision/'.format(pk=instance.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('instance.github.get_commit_id_from_ref')
    def test_provision_github_branch_deleted(self, mock_get_commit_id_from_ref):
        """
        POST /:id/provision - GitHub returns 404 response for instance branch
        """
        self.api_client.login(username='user1', password='pass')
        instance = OpenEdXInstanceFactory()
        mock_get_commit_id_from_ref.side_effect = github.ObjectDoesNotExist
        response = self.api_client.post('/api/v1/openedxinstance/{pk}/provision/'.format(pk=instance.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('instance.github.get_commit_id_from_ref')
    @patch('instance.api.instance.provision_instance')
    def test_provision(self, mock_provision_instance, mock_get_commit_id_from_ref):
        """
        POST /:id/provision
        """
        self.api_client.login(username='user1', password='pass')
        instance = OpenEdXInstanceFactory(commit_id='0' * 40, branch_name='api-branch', fork_name='api/repo')
        OpenStackServerFactory(instance=instance,
                               status=OpenStackServer.Status.Ready,
                               progress=OpenStackServer.Progress.Success)
        mock_get_commit_id_from_ref.return_value = '1' * 40

        response = self.api_client.post('/api/v1/openedxinstance/{pk}/provision/'.format(pk=instance.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'status': 'Instance provisioning started'})
        self.assertEqual(mock_provision_instance.call_count, 1)
        self.assertEqual(OpenEdXInstance.objects.get(pk=instance.pk).commit_id, '1' * 40)
        self.assertEqual(mock_get_commit_id_from_ref.mock_calls, [
            call('api/repo', 'api-branch', ref_type='heads'),
        ])

    def test_get_log_entries(self):
        """
        GET - Log entries
        """
        self.api_client.login(username='user1', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain='instance0')
        server = OpenStackServerFactory(openstack_id="vm0", instance=instance)
        instance.logger.info("info")
        instance.logger.error("error")
        server.logger.info("info")
        server.logger.error("error")

        response = self.api_client.get('/api/v1/openedxinstance/{pk}/'.format(pk=instance.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_list = [
            {'level': 'INFO', 'text': 'instance.models.instance  | instance=instance0 | info'},
            {'level': 'ERROR', 'text': 'instance.models.instance  | instance=instance0 | error'},
            {'level': 'INFO', 'text': 'instance.models.server    | instance=instance0,server=vm0 | info'},
            {'level': 'ERROR', 'text': 'instance.models.server    | instance=instance0,server=vm0 | error'},
        ]
        self.assertEqual(len(expected_list), len(response.data['log_entries']))

        for expected_entry, log_entry in zip(expected_list, response.data['log_entries']):
            self.assertEqual(expected_entry['level'], log_entry['level'])
            self.assertEqual(expected_entry['text'], log_entry['text'])

    def test_get_log_error_entries(self):
        """
        GET - Log error entries
        """
        self.api_client.login(username='user1', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain='instance0')
        server = OpenStackServerFactory(openstack_id="vm0", instance=instance)
        instance.logger.info("info")
        instance.logger.error("error")
        server.logger.info("info")
        server.logger.error("error")

        response = self.api_client.get('/api/v1/openedxinstance/{pk}/'.format(pk=instance.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_list = [
            {'level': 'ERROR', 'text': 'instance.models.instance  | instance=instance0 | error'},
            {'level': 'ERROR', 'text': 'instance.models.server    | instance=instance0,server=vm0 | error'},
        ]
        self.assertEqual(len(expected_list), len(response.data['log_error_entries']))

        for expected_entry, log_entry in zip(expected_list, response.data['log_error_entries']):
            self.assertEqual(expected_entry['level'], log_entry['level'])
            self.assertEqual(expected_entry['text'], log_entry['text'])
