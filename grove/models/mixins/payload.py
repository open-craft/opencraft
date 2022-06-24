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
Grove instance app model mixins - Payload
"""

# Imports #####################################################################


from typing import Any, Dict
import yaml

from django.contrib.postgres.fields import JSONField
from django.utils.text import slugify
from django.db import models

from grove.models.mixins.configurationshim import AnsibleConfigurationShim

# Classes #####################################################################


class PayloadMixin(models.Model, AnsibleConfigurationShim):
    """
    Mixin to prepare the Grove trigger payload
    """

    overrides = JSONField(null=True, blank=True)

    class Meta:
        abstract = True

    def build_trigger_payload(self) -> Dict[str, Any]:
        """
        Assemble the payload for the GitLab pipeline to trigger a new deployment.
        """
        grove_instance = self.instance.instance
        payload = {
            "variables": {
                "INSTANCE_NAME": slugify(grove_instance.name),
                "DEPLOYMENT_REQUEST_ID": str(self.pk),
                "NEW_INSTANCE_TRIGGER": "1"
            }
        }

        # Build and append different configuration information to the payload
        payload.update(self._build_hostname_payload(grove_instance))
        payload.update(self._build_theme_payload(grove_instance))
        payload.update(self._build_site_configuration_payload(grove_instance))
        payload.update(self._build_instance_env_configuration_payload(grove_instance))

        payload.update(self.overrides or {})
        return payload

    def _build_hostname_payload(self, instance) -> Dict[str, Any]:
        """
        Build payload with all hostname details.
        """
        hostname_payload = {
            "TUTOR_LMS_HOST": instance.external_lms_domain or instance.internal_lms_domain,
            "TUTOR_PREVIEW_LMS_HOST": instance.external_lms_preview_domain or instance.internal_lms_preview_domain,
            "TUTOR_CMS_HOST": instance.external_studio_domain or instance.internal_studio_domain,
            "TUTOR_DISCOVERY_HOST": instance.external_discovery_domain or instance.internal_discovery_domain,
            "TUTOR_ECOMMERCE_HOST": instance.external_ecommerce_domain or instance.internal_ecommerce_domain,
            "TUTOR_MFE_HOST": instance.external_mfe_domain or instance.internal_mfe_domain
        }
        return hostname_payload

    def _build_theme_payload(self, instance) -> Dict[str, Any]:
        """
        Build payload with theme repo details and theme customizations.
        """
        grove_theme_settings = {}
        theme_settings = yaml.load(instance.get_theme_settings(), Loader=yaml.SafeLoader)

        if theme_settings:
            grove_theme_settings = {
                "GROVE_COMPREHENSIVE_THEME_NAME": theme_settings.get("EDXAPP_DEFAULT_SITE_THEME"),
                "GROVE_COMPREHENSIVE_THEME_SOURCE_REPO": theme_settings.get("EDXAPP_COMPREHENSIVE_THEME_SOURCE_REPO"),
                "GROVE_COMPREHENSIVE_THEME_VERSION": theme_settings.get("EDXAPP_COMPREHENSIVE_THEME_VERSION"),
                "GROVE_SIMPLE_THEME_SCSS_OVERRIDES": theme_settings.get("SIMPLETHEME_SASS_OVERRIDES", []),
                "GROVE_SIMPLE_THEME_EXTRA_SCSS": theme_settings.get("SIMPLETHEME_EXTRA_SASS", ""),
                "GROVE_SIMPLE_THEME_STATIC_FILES_URLS": theme_settings.get("SIMPLETHEME_STATIC_FILES_URLS", [])
            }

        return grove_theme_settings

    def _build_site_configuration_payload(self, instance) -> Dict[str, Any]:
        """
        Build payload with site configurations settings.
        """
        grove_site_configuration = {}
        site_configuration_settings = yaml.load(instance.get_site_configuration_settings(), Loader=yaml.SafeLoader)

        if site_configuration_settings:
            grove_site_configuration = {
                "TUTOR_SITE_CONFIG": site_configuration_settings.get('EDXAPP_SITE_CONFIGURATION')[0].get("values")
            }

        return grove_site_configuration

    def _build_instance_env_configuration_payload(self, instance) -> Dict[str, Any]:
        """
        Build payload with env and feature configurations.
        """
        grove_env_configuration = {}

        configuration_extra_settings = yaml.load(instance.configuration_extra_settings, Loader=yaml.SafeLoader)

        if configuration_extra_settings:
            grove_env_configuration = {
                "ENV_LMS": configuration_extra_settings.get("EDXAPP_LMS_ENV", {}),
                "ENV_LMS_FEATURES": configuration_extra_settings.get("EDXAPP_LMS_ENV_FEATURES", {}),
                "ENV_CMS": configuration_extra_settings.get("EDXAPP_CMS_ENV", {}),
                "ENV_CMS_FEATURES": configuration_extra_settings.get("EDXAPP_CMS_ENV_FEATURES", {}),
                "ENV_COMMON_FEATURES": configuration_extra_settings.get("EDXAPP_COMMON_ENV_FEATURES", {})
            }

            # Parse old ansible configuration settings and append settings to payload.
            self.parse_ansible_configuration(grove_env_configuration, configuration_extra_settings)

        return grove_env_configuration

    def build_abort_pipeline_trigger_payload(self, pipeline_id) -> Dict[str, Any]:
        """
        Assemble the deployment pipeline cancellation payload.
        """
        return {
            "variables[ABORT_DEPLOYMENT_TRIGGER]": True,
            "variables[PIPELINE_ID]": pipeline_id,
        }
