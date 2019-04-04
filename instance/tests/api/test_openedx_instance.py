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

import ddt
from django.conf import settings
from rest_framework import status

from instance.tests.api.base import APITestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.openedx_appserver import make_test_appserver


# Tests #######################################################################

@ddt.ddt
class OpenEdXInstanceAPITestCase(APITestCase):
    """
    Test cases for Instance API calls. Checks data that is specific to OpenEdXInstance
    """

    @ddt.data('user3', 'user4')
    def test_get_authenticated(self, username):
        """
        GET - Authenticated - instance manager user (superuser or not) is allowed access
        """
        self.api_client.login(username=username, password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.data, [])

        # Both user3 (superuser) and user4 (non-superuser) will see user4's instance
        instance = OpenEdXInstanceFactory(sub_domain='domain.api')
        instance.ref.creator = self.user4.profile
        instance.ref.owner = self.user4.profile.organization
        instance.save()

        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance_data = response.data[0].items()
        self.assertIn(('domain', 'domain.api.example.com'), instance_data)
        self.assertIn(('is_archived', False), instance_data)
        self.assertIn(('appserver_count', 0), instance_data)
        self.assertIn(('active_appservers', []), instance_data)
        self.assertIn(('is_healthy', None), instance_data)
        self.assertIn(('is_steady', None), instance_data)
        self.assertIn(('status_description', ''), instance_data)
        self.assertIn(('newest_appserver', None), instance_data)

    def test_get_unauthenticated(self):
        """
        GET - Require to be authenticated in order to see the instance list.
        """
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "Authentication credentials were not provided."})

    @ddt.data('user1', 'user2')
    def test_get_permission_denied(self, username):
        """
        GET - basic and staff users denied access to the instance list.
        """
        self.api_client.login(username=username, password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {"detail": "You do not have permission to perform this action."})

    def add_active_appserver(self, sub_domain='domain.api'):
        """
        Create an instance, and add an active appserver.
        """
        self.api_client.login(username='user3', password='pass')
        instance = OpenEdXInstanceFactory(sub_domain=sub_domain)
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
        self.assertIn(('is_archived', False), instance_data)
        self.assertIn(('url', 'https://domain.api.example.com/'), instance_data)
        self.assertIn(('studio_url', 'https://studio.domain.api.example.com/'), instance_data)
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

    def test_instance_list_admin(self):
        """
        Instance list should return all instances when queried from an admin
        user.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.com')
        # User 3 belongs to organization 2
        instance.ref.owner = self.organization2
        instance.save()
        instance2 = OpenEdXInstanceFactory(sub_domain='test2.com')
        # ... not to organization 1
        instance2.ref.owner = self.organization
        instance2.save()
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(len(response.data), 2)

    def test_instance_list_non_admin_same_organization(self):
        """
        Instance list should return instance for the organization the
        user belongs to.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.com')
        # User 4 belongs to organization 2
        instance.ref.owner = self.organization2
        instance.save()
        self.api_client.login(username='user4', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(len(response.data), 1)

    def test_instance_list_non_admin_different_org(self):
        """
        A non-admin user shouldn't see an instance which belongs to a different organization.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.com')
        # User 4 belongs to organization 2, but instance belongs to organization 1
        instance.ref.owner = self.organization
        instance.save()
        self.api_client.login(username='user4', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(len(response.data), 0)

    def test_instance_list_user_no_organization(self):
        """
        Instance list should be empty if user doesn't belong to an organization.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.com')
        instance.ref.owner = self.organization
        instance.save()
        # User 5 doesn't belong to any organization
        self.api_client.login(username='user5', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(len(response.data), 0)

    def test_instance_list_efficiency(self):
        """
        The number of database queries required to fetch /api/v1/instance/
        should be O(1)
        """
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/instance/')
        self.assertEqual(len(response.data), 0)

        # The 7 queries are:
        # Session, User, InstanceReference, OpenEdXInstance, InstanceReference, OpenEdxAppServer, OpenEdxAppServer
        # Because user3 is superuser, his UserProfile/Organization need not be fetched to detect he's admin,
        # so in this test we save some queries compared to a non-superuser User.
        queries_per_api_call = 7

        for num_instances in range(1, 4):
            self.add_active_appserver(sub_domain='api{}'.format(num_instances))
            try:
                with self.assertNumQueries(queries_per_api_call):
                    response = self.api_client.get('/api/v1/instance/')
            except AssertionError:
                # The above assertion error alone won't indicate the number of
                # instances at the time the assertion was thrown, so state that:
                msg = "Expect query count to be {} when retrieving list of {} instances".format(
                    queries_per_api_call, num_instances
                )
                raise AssertionError(msg)
            self.assertEqual(len(response.data), num_instances)

    def test_newest_appserver(self):
        """
        GET - instance list - is 'newest_appserver' in fact the newest one?
        """
        instance, dummy = self.add_active_appserver()

        mid_app_server = make_test_appserver(instance)
        mid_app_server.is_active = True
        mid_app_server.save()  # Outside of tests, use app_server.make_active() instead

        newest_appserver = make_test_appserver(instance)

        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/instance/')

        self.assertEqual(response.data[0]['newest_appserver']['id'], newest_appserver.id)

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
