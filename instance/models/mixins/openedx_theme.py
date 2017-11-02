# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2017 OpenCraft <xavier@opencraft.com>
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
from django.conf import settings
from django.db import models
from django.template import loader


# Classes #####################################################################

class OpenEdXThemeMixin:
    """
    Mixin that provides functionality required for the storage backends that an OpenEdX
    Instance uses (when not using ephemeral databases)
    """

    class Meta:
        abstract = True

    def get_theme_settings(self):
        """
        Returns a text string with ansible variables for design fields (colors, logo, ...)
        in YAML format, to be passed to configuration_theme_settings.
        """

        template = loader.get_template('instance/ansible/simple_theme.yml')

        # application can be None (for instances not created through the form) or a
        # BetaTestApplication object. first() returns None or object.
        application = self.betatestapplication_set.first()
        design_fields_yaml = template.render(
            dict(
                application=application,
            )
        )
        return design_fields_yaml
