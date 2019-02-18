# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
OpenEdXInstance Theme Mixins - Tests
"""

# Imports #####################################################################

import yaml
from django.contrib.auth import get_user_model

from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from registration.models import BetaTestApplication


# Tests #######################################################################

class OpenEdXThemeMixinTestCase(TestCase):
    """
    Tests for OpenEdXThemeMixin, to check that settings from the beta application form are
    correctly transformed into ansible variables.
    """

    @staticmethod
    def make_test_application(instance, user):
        """
        Creates BetaTestApplication with test data and sample colors.
        """
        application = BetaTestApplication.objects.create(
            subdomain='test',
            instance_name='That username is mine',
            public_contact_email='test@example.com',
            project_description='test',
            user=user,
            instance=instance,
            main_color='#001122',
            link_color='#003344',
            header_bg_color='#caaffe',
            footer_bg_color='#ffff11',
            logo='opencraft_logo_small.png',
            favicon='favicon.ico',
        )
        return application

    def test_colors_and_images_applied(self):
        """
        Creates a beta application with asks for some colors and logo/favicon, and checks that the generated
        ansible variables match those colors and images.
        """
        # Create objects
        OpenEdXInstanceFactory(name='Integration - test_colors_applied', deploy_simpletheme=True)
        instance = OpenEdXInstance.objects.get()
        user = get_user_model().objects.create_user('betatestuser', 'betatest@example.com')
        self.make_test_application(instance, user)
        appserver = make_test_appserver(instance)

        # Test the results
        self.assertTrue(instance.deploy_simpletheme)
        # We check 2 times: one time just the theme vars, next whether they're in the final list
        ansible_theme_vars = instance.get_theme_settings()
        ansible_vars = appserver.configuration_settings
        for variables in (ansible_theme_vars, ansible_vars):
            parsed_vars = yaml.load(variables) or {}
            expected_settings = {
                'SIMPLETHEME_ENABLE_DEPLOY': True,
                'SIMPLETHEME_SASS_OVERRIDES': [
                    {'variable': 'link-color',
                     'value': '#003344', },
                    {'variable': 'header-bg',
                     'value': '#caaffe', },
                    {'variable': 'footer-bg',
                     'value': '#ffff11', },
                    {'variable': 'button-color',
                     'value': '#001122', },
                    {'variable': 'action-primary-bg',
                     'value': '#001122', },
                    {'variable': 'action-secondary-bg',
                     'value': '#001122', },
                    {'variable': 'theme-colors',
                     'value': '("primary": #001122, "secondary": #001122)'}
                ],
                'EDXAPP_DEFAULT_SITE_THEME': 'simple-theme',
                # for SIMPLETHEME_STATIC_FILES_URLS, see below
                'SIMPLETHEME_EXTRA_SASS': """
                $main-color: #001122;
                $link-color: #003344;
                $header-bg: #caaffe;
                $header-font-color: #000000;
                $footer-bg: #ffff11;
                $footer-font-color: #000000;
            """
            }
            for ansible_var, value in expected_settings.items():
                self.assertEqual(value, parsed_vars[ansible_var])

            # We check that the files are in URLs
            # If this fails in local tests it can be because you don't have SWIFT upload enabled
            # (check the .env or .env.test file for MEDIAFILES_SWIFT_ENABLE and login info)
            files = parsed_vars['SIMPLETHEME_STATIC_FILES_URLS']
            self.assertEqual(len(files), 2)
            logo, favicon = files
            self.assertEqual(logo['dest'], 'lms/static/images/logo.png')
            self.assertEqual(favicon['dest'], 'lms/static/images/favicon.ico')
            self.assertIn('opencraft_logo_small.png', logo['url'])
            self.assertIn('favicon.ico', favicon['url'])

    def test_simpletheme_optout(self):
        """
        Test that opting out from simple_theme deployment produces no theme-related ansible vars.
        This feature is used by instances prior to simple_theme, so that they keep using the default
        theme.
        """
        # Create objects. Note the deploy_simpletheme=False
        OpenEdXInstanceFactory(name='Integration - test_simpletheme_optout', deploy_simpletheme=False)
        instance = OpenEdXInstance.objects.get()
        user = get_user_model().objects.create_user('betatestuser', 'betatest@example.com')
        self.make_test_application(instance, user)
        appserver = make_test_appserver(instance)

        # Test the results
        ansible_theme_vars = instance.get_theme_settings()
        ansible_vars = appserver.configuration_settings
        for variables in (ansible_theme_vars, ansible_vars):
            parsed_vars = yaml.load(variables) or {}
            self.assertNotIn('SIMPLETHEME_ENABLE_DEPLOY', parsed_vars)
            self.assertNotIn('SIMPLETHEME_SASS_OVERRIDES', parsed_vars)
            self.assertNotIn('EDXAPP_DEFAULT_SITE_THEME', parsed_vars)
