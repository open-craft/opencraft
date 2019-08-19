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
Decorators - Tests
"""

# Imports #####################################################################

import ddt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.urls import reverse

from instance.tests.base import WithUserTestCase
from instance.views.decorators import instance_manager_required


# Tests #######################################################################

@ddt.ddt
class InstanceManagerDecoratorTests(WithUserTestCase):
    """
    Test cases for instance_manager_required
    """
    url = reverse('instance:index')
    login_url = reverse(settings.LOGIN_URL)
    register_url = reverse('registration:register')

    """
    Tests for the permission_required decorator
    """
    def setUp(self):
        """Create the request factory"""
        super(InstanceManagerDecoratorTests, self).setUp()
        self.factory = RequestFactory()

    def test_anonymous_login(self):
        """Ensure that anonymous users are redirected to login"""
        @instance_manager_required
        def a_view(request):
            """Test view"""
            return HttpResponse()
        request = self.factory.get('/rand')
        request.user = AnonymousUser()
        response = a_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    @ddt.data('user1', 'user2')
    def test_user_login(self, username):
        """Ensure that basic and staff users are redirected to login"""
        @instance_manager_required
        def a_view(request):
            """Test view"""
            return HttpResponse()
        request = self.factory.get('/rand')
        request.user = getattr(self, username)
        response = a_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.login_url, response.url)

    def test_instance_manager_succeeds(self):
        """Ensure that instance manager users are allowed in"""
        @instance_manager_required
        def a_view(request):
            """Test view"""
            return HttpResponse()
        request = self.factory.get('/rand')
        request.user = self.user3
        response = a_view(request)
        self.assertEqual(response.status_code, 200)

    def test_permissioned_denied_exception_raised(self):
        """Ensure that PermissionDenied is raised when requested"""
        @instance_manager_required(raise_exception=True)
        def a_view(request):
            """Test view"""
            return HttpResponse()
        request = self.factory.get('/rand')
        request.user = self.user1
        with self.assertRaises(PermissionDenied):
            a_view(request)

    def test_redirect_to(self):
        """Ensure that basic users are redirected to redirect_to url"""
        @instance_manager_required(redirect_to=self.register_url)
        def a_view(request):
            """Test view"""
            return HttpResponse()
        request = self.factory.get('/rand')
        request.user = self.user1
        response = a_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.register_url, response.url)
