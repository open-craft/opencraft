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
Theming relates schemas for validating theme configurations.
"""
from django.core.exceptions import ValidationError
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError


color_regex = '^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'


def ref(definition_name):
    """
    Returns the reference to a definition in the same schema.
    """
    return {
        "$ref": "#/definitions/{}".format(definition_name)
    }


nullable_schema = {
    "type": "null",
}

color_schema = {
    "type": "string",
    "pattern": color_regex,
}

flag_schema = {
    "enum": [True, ]
}

theme_schema_v0 = {
    "id": "theme_schema_v0",
    "definitions": {
        "color": color_schema
    },
    "type": "object",
    "properties": {
        "version": {"type": "number", "enum": [0, ]},
        "main_color": ref("color"),
        "link_color": ref("color"),
        "header_bg_color": ref("color"),
        "footer_bg_color": ref("color"),
    },
    "required": ["version", "main_color", "link_color", "header_bg_color", "footer_bg_color"],
    "additionalProperties": False,
}

theme_schema_v1 = {
    "id": "theme_schema_v1",
    "definitions": {
        "color": color_schema,
        "flag": flag_schema,
    },
    "type": "object",
    "properties": {
        "version": {"type": "number", "enum": [1, ]},
        "main-color": ref("color"),
        "link-color": ref("color"),
        "header-bg": ref("color"),
        "footer-bg": ref("color"),
        "footer-color": ref("color"),
        "footer-link-color": ref("color"),
        "btn-primary-bg": ref("color"),
        "btn-primary-color": ref("color"),
        "btn-primary-border-color": ref("color"),
        "btn-primary-hover-bg": ref("color"),
        "btn-primary-hover-color": ref("color"),
        "btn-primary-hover-border-color": ref("color"),
        "btn-secondary-bg": ref("color"),
        "btn-secondary-color": ref("color"),
        "btn-secondary-border-color": ref("color"),
        "btn-secondary-hover-bg": ref("color"),
        "btn-secondary-hover-color": ref("color"),
        "btn-secondary-hover-border-color": ref("color"),
        "accent-color": ref("color"),
        "home-page-hero-title-color": ref("color"),
        "home-page-hero-subtitle-color": ref("color"),
        "customize-sign-in-btn": ref("flag"),
        "btn-sign-in-bg": ref("color"),
        "btn-sign-in-color": ref("color"),
        "btn-sign-in-border-color": ref("color"),
        "btn-sign-in-hover-bg": ref("color"),
        "btn-sign-in-hover-color": ref("color"),
        "btn-sign-in-hover-border-color": ref("color"),
        "customize-register-btn": ref("flag"),
        "btn-register-bg": ref("color"),
        "btn-register-color": ref("color"),
        "btn-register-border-color": ref("color"),
        "btn-register-hover-bg": ref("color"),
        "btn-register-hover-color": ref("color"),
        "btn-register-hover-border-color": ref("color"),
        "customize-logistration-action-btn": ref("flag"),
        "btn-logistration-bg": ref("color"),
        "btn-logistration-color": ref("color"),
        "btn-logistration-border-color": ref("color"),
        "btn-logistration-hover-bg": ref("color"),
        "btn-logistration-hover-color": ref("color"),
        "btn-logistration-hover-border-color": ref("color"),
        "login-register-header-color": ref("color"),
        "main-nav-color": ref("color"),
        "main-nav-link-color": ref("color"),
        "main-nav-item-border-bottom-color": ref("color"),
        "main-nav-item-hover-border-bottom-color": ref("color"),
        "user-dropdown-color": ref("color"),
        "wrapper-preview-menu-color": ref("color"),
        "course-nav-menu-border-bottom-color": ref("color"),
        "account-settings-nav-border-bottom-color": ref("color"),
        "account-settings-nav-hover-border-bottom-color": ref("color"),
    },
    "dependencies": {
        "customize-sign-in-btn": [
            "btn-sign-in-bg",
            "btn-sign-in-color",
            "btn-sign-in-border-color",
            "btn-sign-in-hover-bg",
            "btn-sign-in-hover-color",
            "btn-sign-in-hover-border-color",
        ],
        "customize-register-btn": [
            "btn-register-bg",
            "btn-register-color",
            "btn-register-border-color",
            "btn-register-hover-bg",
            "btn-register-hover-color",
            "btn-register-hover-border-color",
        ],
        "customize-logistration-action-btn": [
            "btn-logistration-bg",
            "btn-logistration-color",
            "btn-logistration-border-color",
            "btn-logistration-hover-bg",
            "btn-logistration-hover-color",
            "btn-logistration-hover-border-color",
        ],
    },
    "required": ["version"],
    "additionalProperties": False,
}

theme_schema = {
    "definitions": {
        "color": {"ref": "#/oneOf/1/color"},
        "flag": {"ref": "#/oneOf/1/flag"},
    },
    "oneOf": [nullable_schema, theme_schema_v0, theme_schema_v1]
}


def theme_schema_validate(value, schema=None):
    """
    Re-raise the schema errors as validation errors so they can be handled
    better by Django.
    """
    try:
        validate(instance=value, schema=schema if schema is not None else theme_schema)
    except JSONSchemaValidationError as e:
        raise ValidationError(message=str(e))
