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
Beta registration browser tests
"""

# Imports #####################################################################

from collections import defaultdict
import re
import time

from django.core.urlresolvers import reverse
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from registration.tests.test_views import BetaTestApplicationViewTestMixin


# Tests #######################################################################

class BetaTestBrowserTestCase(BetaTestApplicationViewTestMixin,
                              StaticLiveServerTestCase):
    """
    Tests the beta test registration flow with a real browser.
    """
    def setUp(self):
        super().setUp()
        self.client = webdriver.Firefox()

    def tearDown(self):
        self.client.quit()
        super().tearDown()

    @property
    def url(self):
        """
        The live server url for the registration page.
        """
        return '{host}{path}'.format(
            host=self.live_server_url,
            path=reverse('registration:register'),
        )

    def form_valid(self):
        """
        Return True if the form is valid, False otherwise.
        """
        return 'ng-valid' in self.form.get_attribute('class').split()

    @property
    def form(self):
        """
        The registration form.
        """
        return self.client.find_element_by_id('registration-form')

    def _get_response_body(self, url):
        """
        Navigate to the given url and return the page body as a string.
        """
        self.client.get(url)
        return self.client.page_source

    def _register(self, form_data):
        """
        Fill in the registration form and click the submit button, if the form
        is valid.
        """
        self.client.get(self.url)

        for field, value in form_data.items():
            element = self.form.find_element_by_name(field)
            if (element.get_attribute('type') == 'checkbox' and
                    bool(value) != element.is_selected()):
                element.click()
            else:
                element.send_keys(value)

        # Wait for ajax validation to complete
        time.sleep(1)

        # If the form is valid, click the submit button and wait for the next
        # page to load
        if self.form_valid():
            submit = self.form.find_element_by_tag_name('button')
            html = self.client.find_element_by_tag_name('html')
            submit.click()
            WebDriverWait(self.client, timeout=3) \
                .until(expected_conditions.staleness_of(html))

        return self.client.page_source

    def _get_error_messages(self, response):
        """
        Get the error messages displayed in the browser.
        """
        selector = 'ul.djng-field-errors'
        error_lists = self.form.find_elements_by_css_selector(selector)
        errors = defaultdict(list)
        for error_list in error_lists:
            pattern = r"(?:form\.(\w+)|form\['(\w+)'\])"
            match = re.match(pattern, error_list.get_attribute('ng-show'))
            name = next(group for group in match.groups() if group)
            for error in error_list.find_elements_by_tag_name('li'):
                if error.is_displayed() and error.text:
                    errors[name].append(error.text)
        return errors
