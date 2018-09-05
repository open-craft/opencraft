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
Login browser tests
"""

# Imports #####################################################################

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.urlresolvers import reverse

from registration.tests.utils import BrowserTestMixin, UserMixin


# Tests #######################################################################

class LoginBrowserTestCase(BrowserTestMixin, UserMixin,
                           StaticLiveServerTestCase):
    """
    Tests the login form with a real browser.
    """
    def test_invalid_credentials(self):
        """
        Check that an error message is displayed when the user submits invalid
        credentials.
        """
        self._login(username=self.username, password='invalid')
        self.assertIn('Please enter a correct username and password',
                      self.form.text)

        # Ensure that the message is still displayed when the user types
        # something into a form field
        self.fill_form({'username': self.username})
        self.assertIn('Please enter a correct username and password',
                      self.form.text)

    def test_valid_credentials(self):
        """
        Check that we're logged in successfully when entering correct credentials.
        """
        self._login(
            username=self.username,
            password=self.password
        )
        # Check that after logging in, we're directed to the registration URL (shared
        # between registration and updating details)
        self.assertEqual(
            self.client.current_url,
            '{host}{path}'.format(
                host=self.live_server_url,
                path=reverse('registration:register'),
            ),
        )
