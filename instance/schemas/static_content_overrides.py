# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <xavier@opencraft.com>
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
Schema for validating the static content overrides data.
"""
from jsonschema import validate

from .utils import nullable_schema, ref

# pylint: disable=invalid-name
static_content_overrides_v0_schema = {
    "definitions": {
        "string": {"type": "string"}
    },
    "type": "object",
    "properties": {
        "version": {"enum": [0, ]},
        "static_template_about_header": ref("string"),
        "static_template_about_content": ref("string"),
        "static_template_contact_header": ref("string"),
        "static_template_contact_content": ref("string"),
        "static_template_donate_header": ref("string"),
        "static_template_donate_content": ref("string"),
        "static_template_tos_header": ref("string"),
        "static_template_tos_content": ref("string"),
        "static_template_honor_header": ref("string"),
        "static_template_honor_content": ref("string"),
        "static_template_privacy_header": ref("string"),
        "static_templates_privacy_content": ref("string"),
    },
    "required": ["version", ],
    "additionalProperties": False
}


static_content_overrides_schema = {
    'definitions': static_content_overrides_v0_schema['definitions'],
    "oneOf": [
        nullable_schema,
        static_content_overrides_v0_schema
    ]
}


def static_content_overrides_schema_validate(value, schema=None):
    """
    Validate the given value against the given schema or the static_content_overrides_schema.
    """
    validate(instance=value, schema=schema if schema is not None else static_content_overrides_schema)
