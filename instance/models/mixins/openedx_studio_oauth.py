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
Open edX studio oauth sso mixin
"""
import functools
import string

from django.db import models
from django.utils.crypto import get_random_string


class OpenEdXStudioOauthMixin(models.Model):
    """
    An instance that configures Studio OAuth2 SSO
    """

    studio_oauth_key = models.CharField(
        max_length=6,
        default=functools.partial(get_random_string, length=6, allowed_chars=string.ascii_lowercase),
        blank=True,
    )
    studio_oauth_secret = models.CharField(
        max_length=32,
        blank=True,
        default=functools.partial(get_random_string, length=32),
    )

    class Meta:
        abstract = True
