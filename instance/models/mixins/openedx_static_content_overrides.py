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
Instance app model mixins -  custom pages
"""

# Imports #####################################################################

from django.contrib.postgres.fields import JSONField
from django.db import models

from instance.schemas.static_content_overrides import static_content_overrides_schema_validate

# Classes #####################################################################


class OpenEdXStaticContentOverridesMixin(models.Model):
    """
    Mixin to provide support for static content overrides.
    """

    class Meta:
        abstract = True

    static_content_overrides = JSONField(
        verbose_name='Static content overrides JSON',
        validators=[static_content_overrides_schema_validate],
        null=True,
        blank=True,
        default=None,
        help_text=("The final static content overrides data committed by the user for deployment. This should be "
                   'picked up the appservers launched for this instance.')
    )
