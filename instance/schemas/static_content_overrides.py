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
import re

from jsonschema import validate

from .utils import nullable_schema, ref

# pylint: disable=invalid-name
static_content_overrides_v0_schema = {
    "definitions": {
        "string": {"type": "string"},
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
        "static_template_privacy_content": ref("string"),
        "homepage_overlay_html": ref("string"),
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

DEFAULT_HERO_TITLE_TEXT = 'Welcome to $instance_name'
DEFAULT_HERO_SUBTITLE_TEXT = 'It works! Powered by Open edX®'

DEFAULT_STATIC_CONTENT_OVERRIDES = {
    "version": 0,
    "homepage_overlay_html": "<h1>{}</h1><p>{}</p>".format(DEFAULT_HERO_TITLE_TEXT, DEFAULT_HERO_SUBTITLE_TEXT)
}

def fill_default_hero_text(text=None):
    """
    Fill in the default hero title and subtitle text in the 'homepage_overlay_html' value if either or both are missing.
    """
    if not text:
        text = DEFAULT_STATIC_CONTENT_OVERRIDES['homepage_overlay_html']
    else:
        homepage_overlay_html_regex = re.compile(
            '^<h1>(?P<title>.*)</h1><p>(?P<subtitle>.*)</p>'
        )
        match = homepage_overlay_html_regex.match(text)
        if match:
            title = match.group('title').strip() or DEFAULT_HERO_TITLE_TEXT
            subtitle = match.group('subtitle').strip() or DEFAULT_HERO_SUBTITLE_TEXT
            text = f'<h1>{title}</h1><p>{subtitle}</p>'
        else:
            text = DEFAULT_STATIC_CONTENT_OVERRIDES['homepage_overlay_html']
    return text


def static_content_overrides_schema_validate(value, schema=None):
    """
    Validate the given value against the given schema or the static_content_overrides_schema.
    """
    validate(instance=value, schema=schema if schema is not None else static_content_overrides_schema)
