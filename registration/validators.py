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
"""Custom password validators for users."""

import re
from django.core.exceptions import ValidationError


class UppercaseValidator:
    """
    Uppercase password validator
    """
    def validate(self, password, user=None):  # pylint: disable=missing-docstring
        if not re.findall('[A-Z]', password):
            raise ValidationError(
                "The password must contain at least 1 uppercase letter, A-Z.",
                code='password_no_upper',
            )

    def get_help_text(self):  # pylint: disable=missing-docstring
        return "Your password must contain at least 1 uppercase letter, A-Z."


class LowercaseValidator:
    """
    Lowercase password validator
    """
    def validate(self, password, user=None):  # pylint: disable=missing-docstring
        if not re.findall('[a-z]', password):
            raise ValidationError(
                "The password must contain at least 1 lowercase letter, a-z.",
                code='password_no_lower',
            )

    def get_help_text(self):  # pylint: disable=missing-docstring
        return "Your password must contain at least 1 lowercase letter, a-z."


class SymbolValidator:
    """
    Symbol password validator
    """
    def validate(self, password, user=None):  # pylint: disable=missing-docstring
        if not re.findall(r'[,.\\!~`<>\/!?:;"+=\-%\'$&@#{}()\[\]_*]', password):
            raise ValidationError(
                "The password must contain at least 1 special character.",
                code='password_no_special_chars',
            )

    def get_help_text(self):  # pylint: disable=missing-docstring
        return "Your password must contain at least 1 special character."
