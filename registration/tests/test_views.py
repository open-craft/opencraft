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

from collections import defaultdict
import json
import re
from unittest.mock import patch

from bs4 import BeautifulSoup
from ddt import data, ddt, unpack
from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from freezegun import freeze_time
from pytz import utc
from simple_email_confirmation.models import EmailAddress

from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from registration.tests.utils import UserMixin


# Tests #######################################################################

class LoginTestCase(UserMixin, TestCase):
    """
    Tests for the login view.
    """
    url = reverse('login')

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
    url = reverse('logout')

    def setUp(self):
        self.client.login(username=self.username, password=self.password)

    def test_redirect(self):
        """
        Test that the logout view redirects to /.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
