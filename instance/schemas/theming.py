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
from schema import Schema, Regex, Optional, Or, SchemaError

color = Regex(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')


def nullable(schema):
    """
    Create new schema that allows the supported schema or None.
    """
    return Or(schema, None)


# #126f9a == $m-blue-d3 in variables.scss. It's rgb(18,111,154)
main_color = '#126f9a'
# Same as main_color. Almost like openedx's #0075b4 == rgb(0, 117, 180)
link_color = '#126f9a'
# openedx also uses white by default
header_bg_color = '#ffffff'
# openedx also uses white by default
footer_bg_color = '#ffffff'

text_color_options = Or('light', 'dark', color)
main_color_options = Or('accent', 'main', color)

button_color_schema = {
    Optional('main'): main_color_options,
    Optional('text'): text_color_options,
    Optional('line'): nullable(main_color_options),
    Optional('hover-main'): main_color_options,
    Optional('hover-text'): text_color_options,
    Optional('hover-line'): nullable(main_color_options),
}

theme_schema_v0 = Schema({
    'version': 0,
    # This is used as the primary color in your theme palette. It is used as filler for buttons.
    Optional('main_color', default=main_color): color,
    # This is used as the color for clickable links on your instance.
    Optional('link_color', default=link_color): color,
    # Header background color: Used as the background color for the top bar.
    Optional('header_bg_color', default=header_bg_color): color,
    # Footer background color: Used as the background color for the footer.
    Optional('footer_bg_color', default=header_bg_color): color,
})

theme_schema_v1 = Schema({
    'version': 1,
    Optional('theme', default='light'): Or('light', 'dark'),
    'colors': {
        Optional('main'): nullable(color),
        Optional('accent'): nullable(color),
        Optional('buttons'): {
            'primary': button_color_schema,
            'secondary': button_color_schema,
        }
    }
})

theme_schema = Or(theme_schema_v0, theme_schema_v1)


def theme_schema_validate(value):
    """
    Re-raise the schema errors as validation errors so they can be handled
    better by Django.
    """
    try:
        theme_schema.validate(value)
    except SchemaError as e:
        raise ValidationError(message=str(e))
