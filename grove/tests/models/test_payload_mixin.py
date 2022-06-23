# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2022 OpenCraft <contact@opencraft.com>
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
GitlabPipeline model - Tests
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.test import TestCase
import factory

from grove.tests.models.factories.grove_deployment import GroveDeploymentFactory
from grove.tests.models.factories.grove_instance import GroveInstanceFactory
from instance.models.deployment import DeploymentType
from registration.models import BetaTestApplication


class GrovePayloadMixinTestCase(TestCase):
    """
    Tests for PayloadMixin
    """

    LMS_HOSTNAME = 'sample.example.org'
    CMS_HOSTNAME = 'studio.sample.example.org'

    def setup_instance(self):
        """
        Creates test instance and corresponding BetaTestApplication and Deployment.
        """
        instance = GroveInstanceFactory(
            internal_lms_domain=self.LMS_HOSTNAME,
            internal_studio_domain=self.CMS_HOSTNAME,
            edx_platform_commit=settings.DEFAULT_OPENEDX_RELEASE,
            deploy_simpletheme=True,
            configuration_extra_settings="""
                EDXAPP_LMS_ENV:
                    DCS_SESSION_COOKIE_SAMESITE: Lax
                EDXAPP_LMS_ENV_FEATURES:
                    ENABLE_CREATOR_GROUP: true
                EDXAPP_CMS_ENV:
                    SESSION_ENGINE: django.contrib.sessions.backends.cached_db
                EDXAPP_CMS_ENV_FEATURES:
                    ENABLE_BULK_ENROLLMENT_VIEW: true
                EDXAPP_COMMON_ENV_FEATURES:
                    ENABLE_COUNTRY_ACCESS: true
                EDXAPP_LOG_LEVEL: info
                EDXAPP_PDF_RECEIPT_TAX_ID: TAX123
                EDXAPP_CMS_STATIC_URL_BASE: http://static.example.com
                EDXAPP_ENABLE_MKTG_SITE: true
            """
        )
        user = get_user_model().objects.create_user('betatestuser', 'betatest@example.com')
        instance_type = ContentType.objects.get_for_model(instance)
        BetaTestApplication.objects.create(
            subdomain='test',
            instance_name='That username is mine',
            public_contact_email='test@example.com',
            project_description='test',
            user=user,
            instance_type=instance_type,
            instance_id=instance.id,
            main_color='#001122',
            link_color='#003344',
            header_bg_color='#caaffe',
            footer_bg_color='#ffff11',
            logo='opencraft_logo_small.png',
            favicon='favicon.ico',
        )
        deployment = GroveDeploymentFactory(instance=instance.ref, type=DeploymentType.admin)
        return deployment.build_trigger_payload()

    @factory.django.mute_signals(post_save)
    def execute_payload_test(self, expected_settings):
        """
        Setup instance and test payload content.
        """
        payload = self.setup_instance()
        for key, value in expected_settings.items():
            self.assertEqual(value, payload[key])

    def test_basic_trigger_payload(self):
        """
        Test instance details are correctly set in payload.
        """
        expected_settings = {
            "variables": {
                "DEPLOYMENT_REQUEST_ID": "1",
                "NEW_INSTANCE_TRIGGER": "1"
            }
        }
        payload = self.setup_instance()
        for key, value in expected_settings["variables"].items():
            self.assertEqual(value, payload["variables"][key])
        self.assertIn("test-grove-instance-", payload["variables"]["INSTANCE_NAME"])

    def test_hostname_payload(self):
        """
        Test hostnames are correctly set in payload.
        """
        expected_settings = {
            "TUTOR_LMS_HOST": self.LMS_HOSTNAME,
            "TUTOR_CMS_HOST": self.CMS_HOSTNAME,
        }
        self.execute_payload_test(expected_settings)

    def test_theme_payload(self):
        """
        Test theme details are correctly set in payload.
        """
        expected_settings = {
            'GROVE_COMPREHENSIVE_THEME_SOURCE_REPO': settings.SIMPLE_THEME_SKELETON_THEME_LEGACY_REPO,
            'GROVE_COMPREHENSIVE_THEME_VERSION': settings.SIMPLE_THEME_SKELETON_THEME_LEGACY_VERSION,
            'GROVE_SIMPLE_THEME_SCSS_OVERRIDES': [
                {'variable': 'link-color',
                 'value': '#003344', },
                {'variable': 'button-color',
                 'value': '#001122', },
                {'variable': 'action-primary-bg',
                 'value': '#001122', },
                {'variable': 'action-secondary-bg',
                 'value': '#001122', },
                {'variable': 'theme-colors',
                 'value': '("primary": #001122, "secondary": #001122)'}
            ],
            'GROVE_COMPREHENSIVE_THEME_NAME': 'simple-theme',
            'GROVE_SIMPLE_THEME_EXTRA_SCSS': """
                $main-color: #001122;
                $link-color: #003344;
                $header-bg: #caaffe;
                $header-font-color: #000000;
                $footer-bg: #ffff11;
                $footer-font-color: #000000;
            """
        }
        self.execute_payload_test(expected_settings)

    def test_site_configuration_payload(self):
        """
        Test site configuration details are correctly set in payload.
        """
        expected_settings = {
            "TUTOR_SITE_CONFIG": {
                'CONTACT_US_CUSTOM_LINK': '/contact',
                'ENABLE_LEARNER_RECORDS': False
            }
        }
        self.execute_payload_test(expected_settings)

    def test_env_configuration_payload(self):
        """
        Test lms and cms env config details are correctly set in payload.
        """
        expected_settings = {
            "ENV_LMS": {
                "DCS_SESSION_COOKIE_SAMESITE": "Lax",
                "LOCAL_LOGLEVEL": "info",
                "PDF_RECEIPT_TAX_ID": "TAX123"
            },
            "ENV_LMS_FEATURES": {
                "ENABLE_CREATOR_GROUP": True
            },
            "ENV_CMS": {
                "SESSION_ENGINE": "django.contrib.sessions.backends.cached_db",
                "LOCAL_LOGLEVEL": "info",
                "STATIC_URL_BASE": "http://static.example.com"
            },
            "ENV_CMS_FEATURES": {
                "ENABLE_BULK_ENROLLMENT_VIEW": True
            },
            "ENV_COMMON_FEATURES": {
                "ENABLE_COUNTRY_ACCESS": True,
                "ENABLE_MKTG_SITE": True
            }
        }
        self.execute_payload_test(expected_settings)
