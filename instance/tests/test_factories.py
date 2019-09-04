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
Factories module - Tests
"""

# Imports #####################################################################

from unittest.mock import patch

from django.conf import settings
from django.test import override_settings
import yaml

from instance.factories import instance_factory, production_instance_factory
from instance.models.log_entry import LogEntry
from instance.models.database_server import MySQLServer, MongoDBServer
from instance.models.mixins.storage import StorageContainer
from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.base import TestCase


# Tests #######################################################################

class FactoriesTestCase(TestCase):
    """
    Test cases for functions in the factories module
    """

    CONFIGURATION_EXTRA_SETTINGS = (
        "{"
        "'demo_test_users': [],"
        "'DEMO_CREATE_STAFF_USER': False,"
        "'SANDBOX_ENABLE_CERTIFICATES': False"
        "}"
    )
    SANDBOX_DEFAULTS = {
        "configuration_version": settings.DEFAULT_CONFIGURATION_VERSION,
        "openedx_release": settings.DEFAULT_OPENEDX_RELEASE,
        "configuration_extra_settings": "",
        "openstack_server_flavor": settings.OPENSTACK_SANDBOX_FLAVOR,
    }
    PRODUCTION_DEFAULTS = {
        "configuration_version": settings.STABLE_CONFIGURATION_VERSION,
        "openedx_release": settings.OPENEDX_RELEASE_STABLE_REF,
        "configuration_extra_settings": CONFIGURATION_EXTRA_SETTINGS,
        "openstack_server_flavor": settings.OPENSTACK_PRODUCTION_INSTANCE_FLAVOR,
    }

    def _assert_field_values(
            self,
            instance,
            sub_domain,
            configuration_version=SANDBOX_DEFAULTS["configuration_version"],
            openedx_release=SANDBOX_DEFAULTS["openedx_release"],
            configuration_extra_settings=SANDBOX_DEFAULTS["configuration_extra_settings"],
            openstack_server_flavor=SANDBOX_DEFAULTS["openstack_server_flavor"],
    ):
        """
        Assert that field values of `instance` match expected values
        """
        self.assertEqual(instance.internal_lms_domain, '{}.example.com'.format(sub_domain))
        self.assertEqual(instance.internal_lms_preview_domain, 'preview.{}.example.com'.format(sub_domain))
        self.assertEqual(instance.internal_studio_domain, 'studio.{}.example.com'.format(sub_domain))
        self.assertEqual(instance.configuration_version, configuration_version)
        self.assertEqual(instance.openedx_release, openedx_release)
        extra_settings = yaml.load(instance.configuration_extra_settings, Loader=yaml.SafeLoader)
        expected_extra_settings = yaml.load(configuration_extra_settings, Loader=yaml.SafeLoader)
        self.assertEqual(extra_settings, expected_extra_settings)

    @patch(
        'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_instance_factory(self, mock_consul):
        """
        Test that factory function for creating instances produces expected results
        """
        # Create instance without changing defaults
        sub_domain = "sandbox-with-defaults"
        instance = instance_factory(sub_domain=sub_domain)
        instance = OpenEdXInstance.objects.get(pk=instance.pk)
        self._assert_field_values(instance, sub_domain)

        # Create instance with custom field values
        sub_domain = "sandbox-customized"
        custom_instance = instance_factory(sub_domain=sub_domain, **self.PRODUCTION_DEFAULTS)
        custom_instance = OpenEdXInstance.objects.get(pk=custom_instance.pk)
        self._assert_field_values(custom_instance, sub_domain, **self.PRODUCTION_DEFAULTS)

        # Calling factory without specifying "sub_domain" should result in an error
        with self.assertRaises(AssertionError):
            instance_factory()

    @patch(
        'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @override_settings(PROD_APPSERVER_FAIL_EMAILS=['appserverfail@localhost'])
    def test_production_instance_factory(self, mock_consul):
        """
        Test that factory function for creating production instances produces expected results
        """
        # Create instance without changing defaults
        sub_domain = "production-instance-with-defaults"
        instance = production_instance_factory(sub_domain=sub_domain)
        instance = OpenEdXInstance.objects.get(pk=instance.pk)
        self._assert_field_values(instance, sub_domain, **self.PRODUCTION_DEFAULTS)
        self.assertEqual(instance.provisioning_failure_notification_emails, ['appserverfail@localhost'])

        # Create instance with custom field values
        sub_domain = "production-instance-customized"
        custom_instance = production_instance_factory(sub_domain=sub_domain, **self.SANDBOX_DEFAULTS)
        custom_instance = OpenEdXInstance.objects.get(pk=custom_instance.pk)
        expected_settings = self.SANDBOX_DEFAULTS.copy()
        expected_settings["configuration_extra_settings"] = self.PRODUCTION_DEFAULTS["configuration_extra_settings"]
        self._assert_field_values(custom_instance, sub_domain, **expected_settings)

        # Create instance that overrides defaults for extra settings
        sub_domain = "production-instance-extra-settings"
        configuration_extra_settings = """
        DEMO_CREATE_STAFF_USER: false
        demo_test_users: []
        SANDBOX_ENABLE_CERTIFICATES: false
        EXTRA_SETTINGS: false
        ADDITIONAL_SETTINGS: true
        """
        expected_settings["configuration_extra_settings"] = configuration_extra_settings
        extra_settings_instance = production_instance_factory(sub_domain=sub_domain, **expected_settings)
        extra_settings_instance = OpenEdXInstance.objects.get(pk=extra_settings_instance.pk)
        self._assert_field_values(extra_settings_instance, sub_domain, **expected_settings)

        # Calling factory without specifying "sub_domain" should result in an error
        with self.assertRaises(AssertionError):
            production_instance_factory()

    def test_production_instance_factory_no_databases(self):
        """
        Test that calling `production_instance_factory` with settings that are problematic
        for production instances produces warnings and does not create production instance.
        """
        # Delete database server objects created during the migrations.
        MySQLServer.objects.all().delete()
        MongoDBServer.objects.all().delete()

        for custom_settings, warning in (
                (
                    {
                        'INSTANCE_STORAGE_TYPE': StorageContainer.S3_STORAGE,
                        'AWS_ACCESS_KEY': None,
                        'AWS_SECRET_ACCESS_KEY': None
                    },
                    (
                        "AWS support is currently enabled. Add AWS_ACCESS_KEY_ID and "
                        "AWS_SECRET_ACCESS_KEY settings or adjust INSTANCE_STORAGE_TYPE setting."
                    ),
                ),
                (
                    {'DEFAULT_INSTANCE_MYSQL_URL': None},
                    (
                        "No MySQL servers configured, and default URL for external MySQL database is missing."
                        "Create at least one MySQLServer, or set DEFAULT_INSTANCE_MYSQL_URL in your .env."
                    ),
                ),
                (
                    {'DEFAULT_INSTANCE_MONGO_URL': None},
                    (
                        "No MongoDB servers configured, and default URL for external MongoDB database is missing."
                        "Create at least one MongoDBServer, or set DEFAULT_INSTANCE_MONGO_URL in your .env."
                    ),
                ),
        ):
            with override_settings(**custom_settings):
                sub_domain = "production-instance-doomed"
                production_instance_factory(sub_domain=sub_domain)
                log_entries = LogEntry.objects.filter(level="WARNING")
                general_entry = log_entries[0]
                setting_entry = log_entries[1]
                self.assertIn(
                    "Environment not ready. Please fix the problems above, then try again. Aborting.",
                    general_entry.text
                )
                self.assertIn(warning, setting_entry.text)
                self.assertFalse(
                    OpenEdXInstance.objects.filter(internal_lms_domain__startswith=sub_domain).exists()
                )
