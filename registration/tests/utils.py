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
Utils for registration tests
"""

# Imports #####################################################################
import time

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.six import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


# Utility Functions ###########################################################


def create_image(filename, size=(48, 48), image_mode='RGB', image_format='png'):
    """
    Generate a test image, returning the filename that it was saved as.
    """
    data = BytesIO()
    Image.new(image_mode, size).save(data, image_format)
    data.seek(0)
    return data


# Classes #####################################################################


class ServerValidationComplete:
    """
    This class will check if the `ng-dirty` class is present, meaning the element was modified, while
    also checking the presence of one of the validation classes is also present to check if server-side
    validation was successful.
    """

    ng_validated_classes = ('ng-valid', 'ng-invalid')

    def __init__(self, locator):
        self.locator = locator

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        classes = element.get_attribute('class').split(' ')
        if 'ng-dirty' in classes and any(ng_class in classes for ng_class in self.ng_validated_classes):
            return element
        return False


class BrowserTestMixin:
    """
    Runs tests with a real browser. Provides helper methods for filling in
    forms. Mix this in with LiveServerTestCase.
    """

    def setUp(self):
        """
        Start firefox.
        """
        super().setUp()
        site = Site.objects.get()
        site.name = 'testing'
        site.domain = self.live_server_url.split('//')[1]
        site.save()
        options = Options()
        options.headless = True
        # Ensure we don't attempt to use the new geckodriver method (which
        # isn't working for us. I _think_ selenium 2 defaults to old method,
        # but just to make sure.
        cap = DesiredCapabilities().FIREFOX
        cap['marionette'] = False
        try:
            self.client = webdriver.Firefox(capabilities=cap, firefox_options=options)
        except WebDriverException:
            time.sleep(1)
            self.client = webdriver.Firefox(capabilities=cap, firefox_options=options)

    def tearDown(self):
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

    def fill_form(self, form_data, validate_fields=None):
        """
        Fill in the form with the given data.
        """
        validate_fields = validate_fields or ()
        for field, value in form_data.items():
            element = self.form.find_element_by_name(field)
            if element.get_attribute('type') == 'checkbox':
                if bool(value) != element.is_selected():
                    element.click()
                    # Before moving on, make sure checkbox state (checked/unchecked) corresponds to desired value
                    WebDriverWait(self.client, timeout=5) \
                        .until(expected_conditions.element_selection_state_to_be(element, value))
                continue

            if element.get_attribute('type') == 'color':
                # Selenium doesn't support typing into HTML5 color field with send_keys
                id_elem = element.get_attribute('id')
                self.client.execute_script("document.getElementById('{}').type='text'".format(id_elem))

            if not element.get_attribute('readonly') and not element.get_attribute('type') == 'hidden':
                element.clear()
                if value:
                    # A small delay is required for angular to properly mark field as dirty
                    element.click()
                    time.sleep(.5)
                    element.send_keys(value)
                    # Before moving on, make sure input field contains desired text
                    WebDriverWait(self.client, timeout=5) \
                        .until(expected_conditions.text_to_be_present_in_element_value((By.NAME, field), value))
                    # And that the server validation, if any, has completed
                    if field in validate_fields:
                        WebDriverWait(self.client, timeout=10) \
                            .until(ServerValidationComplete((By.NAME, field)))

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
            path=reverse('login'),
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

    def setUp(self):
        """
        Create a test user.
        """
        super().setUp()
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
        )
