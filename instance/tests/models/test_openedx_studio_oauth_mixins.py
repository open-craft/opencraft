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
OpenEdXInstance Studio Oauth Mixins - Tests
"""

# Imports #####################################################################

from django.conf import settings

import yaml

from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory


# Tests #######################################################################


class OpenEdXStudioOauthMixinTestCase(TestCase):
    """
    Tests for OpenEdXStudioOauthMixin
    """

    def test_studio_oauth_settings(self):
        """
        Test that Studio Oauth key and secret are generated for instance
        """
        instance = OpenEdXInstanceFactory()
        self.assertIsNot(instance.studio_oauth_key, None)
        self.assertIsNot(instance.studio_oauth_secret, None)

    def _check_generated_settings(self, instance):
        """
        Check required settings are rendered on the appserver
        """
        appserver = make_test_appserver(instance)
        parsed_vars = yaml.load(appserver.configuration_settings, Loader=yaml.SafeLoader)
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_ENV_EXTRA']['SOCIAL_AUTH_EDX_OAUTH2_KEY'],
            instance.studio_oauth_key)
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_ENV_EXTRA']['SOCIAL_AUTH_EDX_OAUTH2_SECRET'],
            instance.studio_oauth_secret)
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_ENV_EXTRA']['SOCIAL_AUTH_EDX_OAUTH2_URL_ROOT'],
            instance.url.rstrip('/'))
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_ENV_EXTRA']['SOCIAL_AUTH_EDX_OAUTH2_PUBLIC_URL_ROOT'],
            instance.url.rstrip('/'))
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_ENV_EXTRA']['SESSION_COOKIE_NAME'],
            settings.STUDIO_SESSION_COOKIE_NAME)
        self.assertIn(
            '{}/logout/'.format(instance.studio_domain),
            parsed_vars['EDXAPP_LMS_ENV_EXTRA']['IDA_LOGOUT_URI_LIST'])
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_SOCIAL_AUTH_EDX_OAUTH2_KEY'],
            instance.studio_oauth_key)
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_SOCIAL_AUTH_EDX_OAUTH2_SECRET'],
            instance.studio_oauth_secret)
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_URL_ROOT'],
            instance.studio_url.rstrip('/'))
        self.assertEqual(
            parsed_vars['EDXAPP_CMS_LOGOUT_URL'],
            '{}logout/'.format(instance.studio_url))

    def test_studio_oauth_master_settings(self):
        """
        Test that Studio Oauth key and secret are passed to the appserver on master
        """
        instance = OpenEdXInstanceFactory()
        self._check_generated_settings(instance)

    def test_studio_oauth_production_settings(self):
        """
        Test that Studio Oauth key and secret are passed to the appserver on Maple
        """
        instance = OpenEdXInstanceFactory(openedx_release=settings.STABLE_EDX_PLATFORM_COMMIT)
        self._check_generated_settings(instance)
