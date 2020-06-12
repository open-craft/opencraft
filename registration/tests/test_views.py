# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Tests for the registration views
"""

# Imports #####################################################################

from django.test import TestCase, override_settings
from django.urls import reverse

from registration.tests.utils import UserMixin

# Tests #######################################################################

class LoginTestCase(UserMixin, TestCase):
    """
    Tests for the login view.
    """
    url = reverse('registration:login')

    @override_settings(INSTANCE_STORAGE_TYPE='s3')
    def test_login(self):
        """
        Test that users can login.
        """
        response = self.client.post(
            path=self.url,
            data={'username': self.username, 'password': self.password},
            follow=True,
        )
        self.assertEqual(response.context['user'], self.user)

    def test_redirect(self):
        """
        Test that users are redirected to / on login.
        """
        response = self.client.post(
            path=self.url,
            data={'username': self.username, 'password': self.password},
        )
        self.assertRedirects(response, '/', fetch_redirect_response=False)


class LogoutTestCase(UserMixin, TestCase):
    """
    Tests for the logout view.
    """
    url = reverse('registration:logout')

    def setUp(self):
        self.client.login(username=self.username, password=self.password)

    def test_logout(self):
        """
        Test that the logout view logs the user out.
        """
        response = self.client.get(self.url, follow=True)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_redirect(self):
        """
        Test that the logout view redirects to /.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
