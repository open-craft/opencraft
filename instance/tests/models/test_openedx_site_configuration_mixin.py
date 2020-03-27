# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <contact@opencraft.com>
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
OpenEdXInstance SiteConfiguration parameters - Tests
"""
# Imports #####################################################################

import yaml

from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory

# Tests #######################################################################


class OpenEdXSiteConfigurationMixinsTestCase(TestCase):
    """
    Tests for the Open edX SiteConfiguration mixin.
    """
    def test_static_content_overrides_unset(self):
        """
        Test that when the static content overrides are unset, there is no SiteConfiguration ansible
        variables are generated. Note that this behaviour will change if there are other sources which
        require setting SiteConfiguration variables.
        """
        instance = OpenEdXInstanceFactory()
        self.assertEqual(instance.get_site_configuration_settings(), '')

    def test_static_content_overrides_set(self):
        """
        Test that when the static content overrides are set, the appropriate ansible variables for setting
        the SiteConfiguration variables are generated. Note that this behaviour will change if there are other
        sources which require setting SiteConfiguration variables.
        """
        instance = OpenEdXInstanceFactory()
        instance.static_content_overrides = {
            'version': 0,
            'static_template_about_content': 'Hello world!',
            'static_template_contact_content': 'Email: nobody@example.com',
            'homepage_overlay_html': 'Welcome to the LMS!',
        }
        instance.save()
        expected_variables = {
            'EDXAPP_SITE_CONFIGURATION': [
                {
                    'values': {
                        'static_template_about_content': 'Hello world!',
                        'static_template_contact_content': 'Email: nobody@example.com',
                        'homepage_overlay_html': 'Welcome to the LMS!',
                    }
                }
            ]
        }
        self.assertEqual(yaml.safe_load(instance.get_site_configuration_settings()), expected_variables)

    def test_unicode_characters_in_static_content_overrides(self):
        """
        Test that when the static content overrides have unicode characters, there are no errors and the expected
        ansible SiteConfiguration variables are generated.
        """
        instance = OpenEdXInstanceFactory()
        instance.static_content_overrides = {
            'version': 0,
            'static_template_about_content': 'வணக்கம்!',
            'homepage_overlay_html': 'வணக்கம்',
        }
        instance.save()
        expected_variables = {
            'EDXAPP_SITE_CONFIGURATION': [
                {
                    'values': {
                        'static_template_about_content': 'வணக்கம்!',
                        'homepage_overlay_html': 'வணக்கம்',
                    }
                }
            ]
        }
        self.assertEqual(yaml.safe_load(instance.get_site_configuration_settings()), expected_variables)

    def test_html_elements_and_attributes_in_static_content_overrides(self):
        """
        Test that when the static content overrides contain html elements and attributes, there are no errors and the
        expected ansible SiteConfiguration variables are generated.
        """
        instance = OpenEdXInstanceFactory()
        instance.static_content_overrides = {
            'version': 0,
            'static_template_about_content': '<p class="paragraph" id=\'hello\'>Hello world!</p>',
            'homepage_overlay_html': '<h1>Welcome to the LMS!</h1>',
        }
        instance.save()
        expected_variables = {
            'EDXAPP_SITE_CONFIGURATION': [
                {
                    'values': {
                        'static_template_about_content': '<p class="paragraph" id=\'hello\'>Hello world!</p>',
                        'homepage_overlay_html': '<h1>Welcome to the LMS!</h1>',
                    }
                }
            ]
        }
        self.assertEqual(yaml.safe_load(instance.get_site_configuration_settings()), expected_variables)
