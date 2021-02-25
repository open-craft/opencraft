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
Test login to the OCIM console
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from simple_email_confirmation.models import EmailAddress

from e2e_tests.tests.utils import BrowserLiveServerTestCase
from instance.tests.base import create_user_and_profile
from registration.models import BetaTestApplication


class LoginTestCase(BrowserLiveServerTestCase):
    """
    LiveServerTest for login
    """

    def setUp(self):
        """
        Setup the user with a BetaTestApplication
        """
        super().setUp()
        self.user_with_app = create_user_and_profile('instance.user', 'instance.user@example.com')
        self.application = BetaTestApplication.objects.create(
            user=self.user_with_app,
            subdomain="somesubdomain",
            instance_name="User's Instance",
            public_contact_email="instance.user.public@example.com",
            privacy_policy_url="http://www.some/url"
        )
        EmailAddress.objects.create_confirmed(
            email=self.application.public_contact_email,
            user=self.user_with_app,
        )

    @property
    def form(self):
        """
        Get the form element on the page
        """
        return self.browser.find_element_by_tag_name("form")

    def test_login_page_success(self):
        """
        Test the successful login behavior
        """
        self.browser.get('http://localhost:3000/login')
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )
        # fill username
        username_field = self.form.find_element_by_name("username")
        username_field.click()
        username_field.send_keys(self.user_with_app.username)
        # fill password
        password_field = self.form.find_element_by_name("password")
        password_field.click()
        password_field.send_keys('pass')

        # click submit
        login_button = self.form.find_element_by_tag_name('button')
        login_button.click()
        self.wait.until(
            EC.url_changes("http://localhost:3000/login")
        )

        # Test we move to theming page
        self.assertEqual(self.browser.current_url, "http://localhost:3000/console/theming/preview-and-colors")

        # Log out user
        self.browser.get('http://localhost:3000/logout')

    def test_login_page_failed(self):
        """
        Test that error message is displayed on wrong credentials
        """
        self.browser.get('http://localhost:3000/login')
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )

        # fill username
        username_field = self.form.find_element_by_name("username")
        username_field.click()
        username_field.send_keys(self.user_with_app.username)
        # fill password
        password_field = self.form.find_element_by_name("password")
        password_field.click()
        password_field.send_keys('wrong_password')

        # click submit
        login_button = self.form.find_element_by_tag_name('button')
        login_button.click()
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        )

        # Check that the page is still login
        self.assertEqual(self.browser.current_url, "http://localhost:3000/login")

        # Check that the error message is displayed
        error_elm = self.browser.find_element_by_class_name("alert-danger")
        self.assertEqual(error_elm.text, "No active account found with the given credentials")
