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
OpenCraft - Views - Tests
"""

# Imports #####################################################################
from unittest import mock

import ddt
from django.conf import settings
from django.urls import reverse
from psycopg2 import OperationalError
from redis.exceptions import ConnectionError as RedisConnectionError
from requests.exceptions import ConnectionError as RequestsConnectionError

from instance.tests.base import TestCase, WithUserTestCase


# Tests #######################################################################

@ddt.ddt
class IndexViewTestCase(WithUserTestCase):
    """
    Test cases for the default opencraft app view
    """
    url = reverse('index')
    login_url = reverse(settings.LOGIN_URL)
    instance_url = reverse('instance:index')
    register_url = login_url
    admin_url = reverse('admin:index')
    admin_login_url = '{}?next={}'.format(reverse('admin:login'), admin_url)

    def test_index_unauthenticated(self):
        """
        Index view - Unauthenticated users go to login page
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, self.login_url)

    @ddt.data('user1', 'user2')
    def test_index_authenticated(self, username):
        """
        Index view - Authenticated basic and staff users
        """
        self.client.login(username=username, password='pass')
        response = self.client.get(self.url)
        self.assertRedirects(response, settings.USER_CONSOLE_FRONTEND_URL, fetch_redirect_response=False)

    def test_index_authenticated_instance_manager(self):
        """
        Index view - Authenticated, staff or instance manager user
        """
        self.client.login(username='user4', password='pass')
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, self.instance_url)
        self.assertContains(response, 'ng-app="InstanceApp"')

    @ddt.data('user1', 'user2')
    def test_login_authenticated(self, username):
        """
        Login view - Authenticate a basic and staff users
        """
        login_data = dict(username=username, password='pass')
        response = self.client.post(self.login_url, login_data)
        self.assertRedirects(response, '/', fetch_redirect_response=False)

    @ddt.data('user3', 'user4')
    def test_login_instance_manager(self, username):
        """
        Login view - Authenticate an instance manager user (superuser or not)
        """
        response = self.client.get(self.login_url)
        login_data = dict(username=username, password='pass')
        response = self.client.post(self.login_url, login_data, follow=True)
        self.assertRedirects(response, self.instance_url)

    @ddt.data(None, 'user1', 'user4')
    def test_admin_permission_denied(self, username):
        """
        Admin view - anonymous, basic and instance manager users go to login page
        """
        if username:
            self.client.login(username=username, password='pass')
        response = self.client.get(self.admin_url, follow=True)
        self.assertRedirects(response, self.admin_login_url)

    @ddt.data('user2', 'user3')
    def test_admin_staff(self, username):
        """
        Index view - staff and superusers see the admin page
        """
        self.client.login(username=username, password='pass')
        response = self.client.get(self.admin_url, follow=True)
        self.assertEqual(response.status_code, 200)


class HealthCheckViewTestCase(TestCase):
    """
    Test cases for the health check view
    """
    url = reverse('health_check')

    @mock.patch('opencraft.views.HealthCheckView._check_postgres_connection', return_value=None)
    @mock.patch('opencraft.views.HealthCheckView._check_redis_connection', return_value=None)
    @mock.patch('opencraft.views.HealthCheckView._check_consul_connection', return_value=None)
    def test_ok(self, mock_postgres, mock_redis, mock_consul):
        """
        Verify 200 response when all services are online
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    @mock.patch('opencraft.views.HealthCheckView._check_postgres_connection', side_effect=OperationalError)
    @mock.patch('opencraft.views.HealthCheckView._check_redis_connection', return_value=None)
    @mock.patch('opencraft.views.HealthCheckView._check_consul_connection', return_value=None)
    def test_postgres_unreachable(self, mock_postgres, mock_redis, mock_consul):
        """
        Verify 503 response when postgres is offline
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content, b'Postgres unreachable')

    @mock.patch('opencraft.views.HealthCheckView._check_postgres_connection', return_value=None)
    @mock.patch('opencraft.views.HealthCheckView._check_redis_connection', side_effect=RedisConnectionError)
    @mock.patch('opencraft.views.HealthCheckView._check_consul_connection', return_value=None)
    def test_redis_unreachable(self, mock_postgres, mock_redis, mock_consul):
        """
        Verify 503 response when redis is offline
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content, b'Redis unreachable')

    @mock.patch('opencraft.views.HealthCheckView._check_postgres_connection', return_value=None)
    @mock.patch('opencraft.views.HealthCheckView._check_redis_connection', return_value=None)
    @mock.patch('opencraft.views.HealthCheckView._check_consul_connection', side_effect=RequestsConnectionError)
    def test_consul_unreachable(self, mock_postgres, mock_redis, mock_consul):
        """
        Verify 503 response when consul is offline
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.content, b'Consul unreachable')
