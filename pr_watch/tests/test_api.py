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
Tests of the Pull Request Watcher API
"""

# Imports #####################################################################

from unittest.mock import patch

import ddt
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.base import WithUserTestCase
from pr_watch import github
from pr_watch.models import WatchedPullRequest
from pr_watch.tests.factories import make_watched_pr_and_instance, PRFactory

# Tests #######################################################################


@ddt.ddt
@patch(
    'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class APITestCase(WithUserTestCase):
    """
    Tests of the Pull Request Watcher API
    """
    def setUp(self):
        super().setUp()

        self.api_factory = APIRequestFactory()
        self.api_client = APIClient()

    def test_get_unauthenticated(self, mock_consul):
        """
        GET - Require to be authenticated
        """
        forbidden_message = {"detail": "Authentication credentials were not provided."}

        response = self.api_client.get('/api/v1/pr_watch/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, forbidden_message)

        watched_pr = make_watched_pr_and_instance()
        response = self.api_client.get('/api/v1/pr_watch/{pk}/'.format(pk=watched_pr.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, forbidden_message)

    @ddt.data('user1', 'user2')
    def test_get_permission_denied(self, username, mock_consul):
        """
        GET - basic and staff users denied access
        """
        forbidden_message = {"detail": "You do not have permission to perform this action."}

        self.api_client.login(username=username, password='pass')
        response = self.api_client.get('/api/v1/pr_watch/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, forbidden_message)

        watched_pr = make_watched_pr_and_instance()
        response = self.api_client.get('/api/v1/pr_watch/{pk}/'.format(pk=watched_pr.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, forbidden_message)

    @ddt.data('user3', 'user4')
    def test_get_authenticated(self, username, mock_consul):
        """
        GET - Authenticated - instance manager users (superuser or not) allowed access
        """
        self.api_client.login(username=username, password='pass')
        response = self.api_client.get('/api/v1/pr_watch/')
        self.assertEqual(response.data, [])

        # This uses user4's organization. Both user3 and user4 will be able to see it later
        watched_pr = make_watched_pr_and_instance(
            branch_name='api-test-branch',
            username='user4',
            organization=self.organization2
        )

        def check_output(data):
            """ Check that the data object passed matches expectations for 'watched_pr' """
            data = data.items()
            self.assertIn(('id', watched_pr.pk), data)
            self.assertIn(('fork_name', 'fork/repo'), data)
            self.assertIn(('target_fork_name', 'source/repo'), data)
            self.assertIn(('branch_name', 'api-test-branch'), data)
            self.assertIn(('github_pr_number', watched_pr.github_pr_number), data)
            self.assertIn(('github_pr_url', watched_pr.github_pr_url), data)
            self.assertIn(('instance_id', watched_pr.instance.ref.id), data)

        response = self.api_client.get('/api/v1/pr_watch/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        check_output(response.data[0])

        # And check the details view:
        response = self.api_client.get('/api/v1/pr_watch/{pk}/'.format(pk=watched_pr.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        check_output(response.data)

    @patch('pr_watch.github.get_commit_id_from_ref', return_value=('5' * 40))
    @patch('pr_watch.github.get_pr_by_number')
    def test_get_filtered_by_organization(self, mock_get_pr_by_number, mock_get_commit_id_from_ref, mock_consul):
        """
        GET+POST - A user (instance manager) can only manage PRs from WF which belong to the user's organization.
        """
        wpr1 = make_watched_pr_and_instance(username='user1', organization=self.organization)
        wpr2 = make_watched_pr_and_instance(username='user4', organization=self.organization2)
        self.assertEqual(WatchedPullRequest.objects.count(), 2)

        # We'll log in with user4, and we should only see pr2, but not pr1
        self.api_client.login(username='user4', password='pass')

        # Check the PR list
        response = self.api_client.get('/api/v1/pr_watch/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(('id', wpr1.pk), response.data[0].items())
        self.assertIn(('id', wpr2.pk), response.data[0].items())

        # Also check the detailed view
        response = self.api_client.get('/api/v1/pr_watch/{pk}/'.format(pk=wpr1.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.api_client.get('/api/v1/pr_watch/{pk}/'.format(pk=wpr2.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Also check update_instance
        mock_get_pr_by_number.return_value = PRFactory(number=wpr1.github_pr_number)
        response = self.api_client.post('/api/v1/pr_watch/{pk}/update_instance/'.format(pk=wpr1.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        mock_get_pr_by_number.return_value = PRFactory(number=wpr2.github_pr_number)
        response = self.api_client.post('/api/v1/pr_watch/{pk}/update_instance/'.format(pk=wpr2.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_organization(self, mock_consul):
        """
        GET+POST - An instance manager without an organization can't see/update any PR.
        """
        self.api_client.login(username='user5', password='pass')
        watched_pr = make_watched_pr_and_instance(branch_name='api-test-branch')

        response = self.api_client.get('/api/v1/pr_watch/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        response = self.api_client.get('/api/v1/pr_watch/{pk}/'.format(pk=watched_pr.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = self.api_client.post('/api/v1/pr_watch/{pk}/update_instance/'.format(pk=watched_pr.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('pr_watch.github.get_pr_by_number')
    @ddt.data('user3', 'user4')
    def test_update_instance(self, username, mock_get_pr_by_number, mock_consul):
        """
        POST /pr_watch/:id/update_instance/ - Update instance with latest settings from the PR
        """
        self.api_client.login(username=username, password='pass')

        # Create a WatchedPullRequest, and OpenEdXInstance:
        watched_pr = make_watched_pr_and_instance(username='user4', organization=self.organization2)

        instance = OpenEdXInstance.objects.get(pk=watched_pr.instance_id)
        self.assertIn('fork/master (5555555)', instance.name)
        self.assertEqual(instance.edx_platform_commit, '5' * 40)

        # Now mock the PR being updated on GitHub
        mock_get_pr_by_number.return_value = PRFactory(
            number=watched_pr.github_pr_number,
            title="Updated Title",
        )

        with patch('pr_watch.github.get_commit_id_from_ref', return_value=('6' * 40)):
            response = self.api_client.post('/api/v1/pr_watch/{pk}/update_instance/'.format(pk=watched_pr.pk))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance.refresh_from_db()
        self.assertEqual(
            instance.name,
            'PR#{}: Updated Title (edx) - fork/master (6666666)'.format(watched_pr.github_pr_number)
        )
        self.assertEqual(instance.edx_platform_commit, '6' * 40)

    def test_update_unauthenticated(self, mock_consul):
        """
        POST /pr_watch/:id/update_instance/ - Denied to anonymous users
        """
        forbidden_message = {"detail": "Authentication credentials were not provided."}

        # Create a WatchedPullRequest, and OpenEdXInstance:
        watched_pr = make_watched_pr_and_instance()

        response = self.api_client.post('/api/v1/pr_watch/{pk}/update_instance/'.format(pk=watched_pr.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, forbidden_message)

    @ddt.data('user1', 'user2')
    def test_update_permission_denied(self, username, mock_consul):
        """
        POST /pr_watch/:id/update_instance/ - Denied to non instance managers (basic user and staff)
        """
        forbidden_message = {"detail": "You do not have permission to perform this action."}

        self.api_client.login(username=username, password='pass')

        # Create a WatchedPullRequest, and OpenEdXInstance:
        watched_pr = make_watched_pr_and_instance()
        response = self.api_client.post('/api/v1/pr_watch/{pk}/update_instance/'.format(pk=watched_pr.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, forbidden_message)

    @patch('pr_watch.github.get_commit_id_from_ref', side_effect=github.ObjectDoesNotExist)
    @patch('pr_watch.github.get_pr_by_number')
    def test_update_instance_branch_delete(self, mock_get_pr_by_number, mock_get_commit_id_from_ref, mock_consul):
        """
        Test what happens when we try to update an instance for a PR whose branch has been
        deleted.

        Note: Once WatchedPullRequest.update_instance_from_pr() has been refactored so that it
        first queries GitHub for PR details (rather than accepting a PR parameter), it can get
        the commit ID from the PR details response, rather than using get_branch_tip(), and then
        this test won't be necessary since the PR API always contains the commit information
        (in ["head"]["sha"]) even if the branch has been deleted.
        """
        self.api_client.login(username='user3', password='pass')

        watched_pr = make_watched_pr_and_instance()
        mock_get_pr_by_number.return_value = PRFactory(number=watched_pr.github_pr_number)
        response = self.api_client.post('/api/v1/pr_watch/{pk}/update_instance/'.format(pk=watched_pr.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Could not fetch updated details from GitHub.'})
