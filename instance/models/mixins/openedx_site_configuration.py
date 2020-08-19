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
Instance app model mixins - SiteConfiguration parameters
"""

import yaml

from django.db import models


class OpenEdXSiteConfigurationMixin(models.Model):
    """
    Mixin to provide the SiteConfiguration parameters to be set on the instance.
    """
    class Meta:
        abstract = True

    def get_site_configuration_settings(self):
        """
        Return the ansible variables to set the SiteConfiguration parameters.
        """
        site_configuration_settings = {
            # default site configuration
            'CONTACT_US_CUSTOM_LINK': '/contact',
        }

        if self.static_content_overrides:
            static_content_overrides = {k: v for k, v in self.static_content_overrides.items() if k != 'version'}
            if static_content_overrides:
                site_configuration_settings.update(static_content_overrides)

        if site_configuration_settings:
            return yaml.dump(
                {'EDXAPP_SITE_CONFIGURATION': [{'values': site_configuration_settings}]},
                default_flow_style=False
            )
        else:
            return ''
