# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <xavier@opencraft.com>
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
Tests for auth backends
"""

# Imports #####################################################################

from django.contrib.auth import authenticate
from django.test import TestCase

from registration.tests.utils import UserMixin


# Tests #######################################################################

class ModelBackendTestCase(UserMixin, TestCase):
    """
    Tests for the custom ModelBackend.
    """
    def test_username_login(self):
        """
        Test that users can login with their username and password.
        """
        self.assertEqual(authenticate(username=self.username, password=self.password), self.user)

    def test_email_login(self):
        """
        Test that users can login with their email address and password.
        """
        self.assertEqual(authenticate(username=self.email, password=self.password), self.user)
