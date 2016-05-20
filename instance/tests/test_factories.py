# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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

from unittest.mock import Mock, patch

from django.conf import settings
import yaml

from instance.factories import instance_factory, production_instance_factory
from instance.models.log_entry import LogEntry
from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.base import TestCase


# Tests #######################################################################

class FactoriesTestCase(TestCase):
    """
    Test cases for functions in the factories module
    """

    CONFIGURATION_EXTRA_SETTINGS = "EXTRA_SETTINGS: true"
    SANDBOX_DEFAULTS = {
        "use_ephemeral_databases": True,
        "configuration_version": settings.DEFAULT_CONFIGURATION_VERSION,
        "openedx_release": settings.DEFAULT_OPENEDX_RELEASE,
        "configuration_extra_settings": "",
    }
    PRODUCTION_DEFAULTS = {
        "use_ephemeral_databases": False,
        "configuration_version": settings.LATEST_OPENEDX_RELEASE,
        "openedx_release": settings.LATEST_OPENEDX_RELEASE,
        "configuration_extra_settings": CONFIGURATION_EXTRA_SETTINGS,
    }

    def _assert_field_values(
            self,
            instance,
            sub_domain,
            use_ephemeral_databases=SANDBOX_DEFAULTS["use_ephemeral_databases"],
            configuration_version=SANDBOX_DEFAULTS["configuration_version"],
            openedx_release=SANDBOX_DEFAULTS["openedx_release"],
            configuration_extra_settings=SANDBOX_DEFAULTS["configuration_extra_settings"]
    ):
        """
        Assert that field values of `instance` match expected values
        """
        self.assertEqual(instance.sub_domain, sub_domain)
        self.assertEqual(instance.use_ephemeral_databases, use_ephemeral_databases)
        self.assertEqual(instance.configuration_version, configuration_version)
        self.assertEqual(instance.openedx_release, openedx_release)
        extra_settings = yaml.load(instance.configuration_extra_settings)
        expected_extra_settings = yaml.load(configuration_extra_settings)
        self.assertEqual(extra_settings, expected_extra_settings)

    def test_instance_factory(self):
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

    @patch("instance.factories.loader")
    def test_production_instance_factory(self, patched_loader):
        """
        Test that factory function for creating production instances produces expected results
        """
        mock_template = Mock()
        mock_template.render.return_value = self.CONFIGURATION_EXTRA_SETTINGS
        patched_loader.get_template.return_value = mock_template

        # Create instance without changing defaults
        sub_domain = "production-instance-with-defaults"
        instance = production_instance_factory(sub_domain=sub_domain)
        instance = OpenEdXInstance.objects.get(pk=instance.pk)
        self._assert_field_values(instance, sub_domain, **self.PRODUCTION_DEFAULTS)
        patched_loader.get_template.assert_called_once_with("instance/ansible/prod-vars.yml")
        mock_template.render.assert_called_once_with({})

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

        # Calling factory with settings that are problematic for production instances should produce warnings
        with patch("instance.factories.settings") as patched_settings:
            patched_settings.SWIFT_ENABLE = False
            patched_settings.INSTANCE_MYSQL_URL = None
            patched_settings.INSTANCE_MONGO_URL = None

            # Ensure that validation passes for configuration_version:
            patched_settings.LATEST_OPENEDX_RELEASE = settings.LATEST_OPENEDX_RELEASE

            production_instance_factory(sub_domain="production-instance-doomed")

            log_entries = LogEntry.objects.all()
            self.assertEqual(len(log_entries), 3)
            self.assertTrue(all(log_entry.level == "WARNING" for log_entry in log_entries))
            self.assertIn("Adjust INSTANCE_MONGO_URL setting.", log_entries[0].text)
            self.assertIn("Adjust INSTANCE_MYSQL_URL setting.", log_entries[1].text)
            self.assertIn("Adjust SWIFT_ENABLE setting.", log_entries[2].text)
