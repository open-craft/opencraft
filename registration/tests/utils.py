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
Utils for registration tests
"""

# Imports #####################################################################

import time

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


# Classes #####################################################################

class BrowserTestMixin:
    """
    Runs tests with a real browser. Provides helper methods for filling in
    forms. Mix this in with LiveServerTestCase.
    """
    def setUp(self): # pylint: disable=invalid-name
        """
        Start firefox.
        """
        super().setUp()
        try:
            self.client = webdriver.Firefox()
        except WebDriverException:
            time.sleep(1)
            self.client = webdriver.Firefox()

    def tearDown(self): # pylint: disable=invalid-name
        """
        Close firefox.
        """
        self.client.quit()
        super().tearDown()

    @property
    def form(self):
        """
        The form on the page.
        """
        return self.client.find_element_by_tag_name('form')

    def fill_form(self, form_data):
        """
        Fill in the form with the given data.
        """
        for field, value in form_data.items():
            element = self.form.find_element_by_name(field)
            if element.get_attribute('type') == 'checkbox':
                if bool(value) != element.is_selected():
                    element.click()
                    # Before moving on, make sure checkbox state (checked/unchecked) corresponds to desired value
                    WebDriverWait(self.client, timeout=5) \
                        .until(expected_conditions.element_selection_state_to_be(element, value))
            elif element.get_attribute('type') == 'color':
                # TODO be able to change colors. Typing in a color chooser doesn't set it. Clicking it opens a
                # dialog but without focus, so typing doesn't help either.
                # element.click()
                # element.send_keys(value)
                pass
            elif not element.get_attribute('readonly') and not element.get_attribute('type') == 'hidden':
                element.clear()
                element.send_keys(value)
                # Before moving on, make sure input field contains desired text
                WebDriverWait(self.client, timeout=5) \
                    .until(expected_conditions.text_to_be_present_in_element_value((By.NAME, field), value))

    def submit_form(self):
        """
        Click the submit button on the form and wait for the next page to
        load.
        """
        html = self.client.find_element_by_tag_name('html')
        submit = self.form.find_element_by_tag_name('button')
        submit.click()
        # Wait for page to start reloading.
        WebDriverWait(self.client, timeout=3) \
            .until(expected_conditions.staleness_of(html))
        # Wait for page to finish reloading.
        WebDriverWait(self.client, timeout=20) \
            .until(lambda driver: driver.execute_script("return document.readyState;") == "complete")

    def _login(self, **kwargs):
        """
        Log in with the given credentials, using the login form.
        """
        login_url = '{host}{path}'.format(
            host=self.live_server_url,
            path=reverse('registration:login'),
        )
        self.client.get(login_url)
        self.fill_form(kwargs)
        self.submit_form()


class UserMixin:
    """
    Provides a test user.
    """
    username = 'tafkap'
    email = 'tafkap@rip.org'
    password = '1999'

    def setUp(self): # pylint: disable=invalid-name
        """
        Create a test user.
        """
        super().setUp()
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
        )
