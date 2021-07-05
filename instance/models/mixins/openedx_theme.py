# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Open edX instance theme mixin, e.g. for simple_theme related settings
"""
import yaml
from colour import Color
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models

from instance.schemas.theming import theme_schema_validate


# Classes #####################################################################

class OpenEdXThemeMixin(models.Model):
    """
    Mixin that provides functionality to customize the look & feel of the UI.

    This:
    1. generates variables for simple_theme, e.g. to change logo/favicon and colors;
    2. customizes the footer logo and link.
    """
    # TODO: Deprecate once new registration flow is in place.
    deploy_simpletheme = models.BooleanField(
        default=False,
        verbose_name='Deploy simple_theme',
        help_text=('If set to True, new appservers will use theme settings from the beta application form, if '
                   'available. A basic theme will be deployed through simple_theme and it may  change colors and '
                   'images. If set to False, no theme will be created and the default Open edX theme will be used; '
                   'this is recommended for instances registered before the theme fields were available.'),
    )
    theme_config = JSONField(
        verbose_name='Final Theme Configuration JSON',
        validators=[theme_schema_validate],
        null=True, blank=True,
        help_text=('The final theme configuration data committed by the user for deployment. This should be picked '
                   'up by appservers launched for this instance'),
    )

    class Meta:
        abstract = True

    def get_simple_theme_static_files_settings(self, application):
        """
        Returns a dict with the keys corresponding to the ansible variables supported by the 'simple-theme' role and
        the values corresponding to the supported values for those variables.
        """

        static_files_settings = [
            {
                "url": application.logo.url,
                "dest": "lms/static/images/logo.png",
            },
            {
                "url": application.favicon.url,
                "dest": "lms/static/images/favicon.ico",
            },
        ]

        if application.hero_cover_image:
            static_files_settings.append({
                "url": application.hero_cover_image.url,
                "dest": "lms/static/images/hero_cover.png"
            })
        return static_files_settings

    def get_common_settings(self, application):
        """
        Returns a dict with the simple-theme settings common to the v0 and v1 implementation.
        """
        return {
            "SIMPLETHEME_ENABLE_DEPLOY": True,
            "SIMPLETHEME_STATIC_FILES_URLS": self.get_simple_theme_static_files_settings(application),
            "EDXAPP_DEFAULT_SITE_THEME": "simple-theme",
        }

    def get_v0_theme_settings(self, application):
        """
        Returns a dict with the ansible SASS variables used by the 'simple-theme' role to deploy the v0 theme. Passed
        to configuration_theme_settings.
        """
        return {
            "EDXAPP_COMPREHENSIVE_THEME_SOURCE_REPO": settings.SIMPLE_THEME_SKELETON_THEME_LEGACY_REPO,
            "EDXAPP_COMPREHENSIVE_THEME_VERSION": settings.SIMPLE_THEME_SKELETON_THEME_LEGACY_VERSION,
            "SIMPLETHEME_SASS_OVERRIDES": [
                {
                    "variable": "link-color",
                    "value": application.link_color,
                },
                {
                    "variable": "button-color",
                    "value": application.main_color,
                },
                {
                    "variable": "action-primary-bg",
                    "value": application.main_color,
                },
                {
                    "variable": "action-secondary-bg",
                    "value": application.main_color,
                },
                {
                    "variable": "theme-colors",
                    "value": "(\"primary\": {primary}, \"secondary\": {secondary})".format(
                        primary=application.main_color,
                        secondary=application.main_color
                    ),
                },
            ],
            "SIMPLETHEME_EXTRA_SASS": """
                $main-color: {main_color};
                $link-color: {link_color};
                $header-bg: {header_bg};
                $header-font-color: {header_font_color};
                $footer-bg: {footer_bg};
                $footer-font-color: {footer_font_color};
            """.format(
                link_color=application.link_color,
                main_color=application.main_color,
                header_bg=application.header_bg_color,
                header_font_color=self.get_contrasting_font_color(
                    application.header_bg_color
                ),
                footer_bg=application.footer_bg_color,
                footer_font_color=self.get_contrasting_font_color(
                    application.footer_bg_color
                ),
            )
        }

    def get_v1_theme_settings(self, application):
        """
        Returns a dict with the ansible SASS variables used by the 'simple-theme' role to deploy the v1 theme. Passed
        to configuration_theme_settings.
        """
        metadata_keys = ('version', 'theme')
        sass_overrides = []
        for key, value in self.theme_config.items():
            if key in metadata_keys:
                continue
            sass_overrides.append({
                'variable': key,
                'value': value
            })

        if application.hero_cover_image:
            sass_overrides.append({
                'variable': 'homepage-bg-image',
                'value': 'url("../images/hero_cover.png")'
            })

        # TODO: map the values in main_variables keys to the appropriate SASS variables
        return {
            "EDXAPP_COMPREHENSIVE_THEME_SOURCE_REPO": settings.SIMPLE_THEME_SKELETON_THEME_REPO,
            "EDXAPP_COMPREHENSIVE_THEME_VERSION": settings.SIMPLE_THEME_SKELETON_THEME_VERSION,
            "SIMPLETHEME_SASS_OVERRIDES": sass_overrides,
            "MFE_DEPLOY_NPM_OVERRIDES": [
                "@edx/brand@file:/edx/var/edxapp/themes/simple-theme/",
            ],
        }

    def get_footer_logo_customizations(self, application):
        """
        Return settings for customizing footer logos.
        """
        footer_logo_customization = {}
        if application.footer_logo_image:
            footer_logo_customization["FOOTER_OPENEDX_LOGO_IMAGE"] = application.footer_logo_image.url
        if application.footer_logo_url:
            footer_logo_customization["FOOTER_OPENEDX_URL"] = application.footer_logo_url
        return {
            "EDXAPP_LMS_ENV_EXTRA": footer_logo_customization,
            "EDXAPP_CMS_ENV_EXTRA": footer_logo_customization
        }

    def get_theme_settings(self):
        """
        Returns a text string with ansible variables for design fields (colors, logo, ...)
        in YAML format, to be passed to configuration_theme_settings.
        """

        if not self.deploy_simpletheme:
            # This is the case e.g. of instances registered before the theme fields were available.
            # We don't change their colors and we don't use simple_theme
            return ""

        # application can be None (for instances not created through the form) or a
        # BetaTestApplication object. first() returns None or object.
        application = self.betatestapplication_set.first()

        if not application:
            # Instance wasn't created from application form, so no colors will be set or changed
            # and simple_theme won't be used (unless manually requested through other settings).
            return ""

        theme_settings = self.get_common_settings(application)

        if self.theme_config:
            sass_customizations = self.get_v1_theme_settings(application)
        else:
            sass_customizations = self.get_v0_theme_settings(application)

        theme_settings.update(sass_customizations)
        theme_settings.update(self.get_footer_logo_customizations(application))
        return yaml.dump(theme_settings, default_flow_style=False)

    @staticmethod
    def get_contrasting_font_color(background_color, delta=0.5):
        """
        Takes in a hexcolor code and returns black or white, depending
        which gives the better contrast
        """
        # Return black if background_color not set
        if not background_color:
            return "#000000"

        try:
            color = Color(background_color)
        except (ValueError, AttributeError):
            return "#000000"

        # Using Web Content Accessibility Guidelines (WCAG) 2.0 and comparing
        # the background to the black color we can define which is the
        # best color to improve readability on the page
        # More info:
        # https://www.w3.org/TR/WCAG20/
        if color.luminance > delta:
            return '#000000'
        else:
            return '#ffffff'
