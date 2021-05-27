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
Utilities for e2e tests
"""
import os
import time
import unittest

from django.conf import settings
from django.test import LiveServerTestCase
from selenium.common.exceptions import WebDriverException
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.ui import WebDriverWait


FIREFOX_BINARY_PATH = os.environ.get("FIREFOX_BINARY_PATH", "/usr/bin/firefox")


@unittest.skipIf(not settings.E2E_TESTS, "Skipping e2e tests")
class BrowserLiveServerTestCase(LiveServerTestCase):
    """
    Test case with browser setup using selenium
    """
    # Set default port to 5000 as it is the port used by api client
    port = 5000

    def setUp(self):
        """
        Setup browser for the e2e tests.
        """
        super().setUp()
        options = Options()
        options.headless = True
        cap = DesiredCapabilities().FIREFOX
        firefox_binary = FirefoxBinary(FIREFOX_BINARY_PATH)
        try:
            self.browser = webdriver.Firefox(capabilities=cap, firefox_options=options, firefox_binary=firefox_binary)
        except WebDriverException:
            time.sleep(1)
            self.browser = webdriver.Firefox(capabilities=cap, firefox_options=options, firefox_binary=firefox_binary)
        self.wait = WebDriverWait(self.browser, 10)

    def tearDown(self):
        """
        Close the browser at the end of test.
        """
        self.browser.quit()
        super().tearDown()
