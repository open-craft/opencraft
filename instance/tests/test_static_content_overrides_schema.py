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
Tests for the static content overrides schema.
"""

import ddt
from jsonschema.exceptions import ValidationError

from instance.schemas.static_content_overrides import (
    DEFAULT_HERO_TITLE_TEXT,
    DEFAULT_HERO_SUBTITLE_TEXT,
    DEFAULT_STATIC_CONTENT_OVERRIDES,
    fill_default_hero_text,
    static_content_overrides_v0_schema,
    static_content_overrides_schema_validate
)
from instance.tests.base import TestCase


@ddt.ddt
class StaticContentOverridesV0SchemaTestCase(TestCase):
    """
    Tests for the static content overrides schema.
    """

    def validate(self, value):
        """
        Validate the given value with the v0 static content overrides schema.
        """
        static_content_overrides_schema_validate(value, schema=static_content_overrides_v0_schema)

    @ddt.data("", None, 1, False, [1, 2, 3, 4], "abcd")
    def test_invalid_data_types(self, value):
        """
        Test that validation fails when passing invalid data types for the value
        """
        with self.assertRaisesRegex(ValidationError, "is not of type 'object'"):
            self.validate(value)

    def test_missing_version(self):
        """
        Test that the validation fails when the value is missing the 'version' property.
        """
        with self.assertRaisesRegex(ValidationError, 'is a required property'):
            self.validate({})

    @ddt.data("", None, 1, False, [1, 2, 3, 4], "abcd")
    def test_invalid_version(self, value):
        """
        Test that the validation fails when the value for 'version' is invalid.
        """
        with self.assertRaisesRegex(ValidationError, 'is not one of.*?0.*'):
            self.validate({'version': value})

    @ddt.data(None, 1, False, [1, 2, 3, 4])
    def test_invalid_values_for_overrides_properties(self, value):
        """
        Test that that validation fails when invalid values are given for the properties.
        """
        for prop in static_content_overrides_v0_schema['properties']:
            if prop == 'version':
                continue
            with self.assertRaisesRegex(ValidationError, "is not of type 'string'"):
                self.validate({'version': 0, prop: value})

    def test_unknown_additional_properties(self):
        """
        Test that the validation fails when unknown additional properties are given.
        """
        with self.assertRaisesRegex(ValidationError, 'Additional properties are not allowed'):
            self.validate({'version': 0, 'foo': 'bar'})

    def test_valid_value(self):
        """
        Test that a valid value passed validation.
        """
        self.validate(
            {
                'version': 0,
                'static_template_about_content': 'Hello world!',
                'homepage_overlay_html': 'Welcome to the LMS!',
            }
        )


@ddt.ddt
class StaticContentOverridesValidationTestCase(TestCase):
    """
    Tests for the static content overrides validation.
    """
    @ddt.data("", 1, False, [1, 2, 3, 4], "abcd")
    def test_invalid_data_types(self, value):
        """
        Test that validation fails when passing invalid data types for the value.
        """
        with self.assertRaisesRegex(ValidationError, 'is not of type'):
            static_content_overrides_schema_validate(value)

    def test_null_accepted(self):
        """
        Test that an empty object is accepted as valid.
        """
        static_content_overrides_schema_validate(None)

    def test_data_in_v0_schema_accepted(self):
        """
        Test that the data validating against the v0 schema is accepted.
        """
        static_content_overrides_schema_validate(
            {
                'version': 0,
                'static_template_about_content': 'Hello world!',
                'homepage_overlay_html': 'Welcome to the LMS!'
            }
        )

    def test_invalid_v0_schema_data(self):
        """
        Test that data with invalid data for the v0 schema causes the validation to fail.
        """
        with self.assertRaisesRegex(ValidationError, "is not of type 'string'"):
            static_content_overrides_schema_validate({'version': 0, 'static_template_about_content': [1, 2, 3]})


@ddt.ddt
class FillDefaultHeroTextTestCase(TestCase):
    """
    Tests for the fill_default_hero_text() function.
    """

    def setUp(self):
        super().setUp()
        self.default_value = DEFAULT_STATIC_CONTENT_OVERRIDES['homepage_overlay_html']

    def test_no_args(self):
        """
        Test that the correct value is returned when no argument is passed.
        """
        self.assertEqual(fill_default_hero_text(), self.default_value)

    def test_arg_empty_string(self):
        """
        Test that the correct value is returned when an empty string is passed
        """
        self.assertEqual(fill_default_hero_text(''), self.default_value)

    def test_arg_string_with_just_whitespace(self):
        """
        Test that the correct value is returned when a string with just whitespace characters.
        """
        self.assertEqual(fill_default_hero_text('    '), self.default_value)

    def test_arg_not_matching_format(self):
        """
        Test that the correct value is returned when a string not matching the expected format is passed.
        """
        self.assertEqual(fill_default_hero_text('ABCD'), self.default_value)

    @ddt.data(
        '',
        '    '
    )
    def test_arg_empty_title_and_subtitle(self, value):
        """
        Test that the correct value is returned when the title and subtitle are empty or have just whitespace
        characters in them.
        """
        self.assertEqual(
            fill_default_hero_text(f'<h1>{value}</h1><p>{value}</p>'),
            self.default_value
        )

    def test_arg_title_or_subtitle_empty(self):
        """
        Test that the correct value is returned when the title or subtitle is empty or just whitespace.
        """
        self.assertEqual(
            fill_default_hero_text('<h1></h1><p>It works!</p>'),
            f'<h1>{DEFAULT_HERO_TITLE_TEXT}</h1><p>It works!</p>'
        )
        self.assertEqual(
            fill_default_hero_text('<h1>    </h1><p>It works!</p>'),
            f'<h1>{DEFAULT_HERO_TITLE_TEXT}</h1><p>It works!</p>'
        )
        self.assertEqual(
            fill_default_hero_text('<h1>It works!</h1><p></p>'),
            f'<h1>It works!</h1><p>{DEFAULT_HERO_SUBTITLE_TEXT}</p>'
        )
        self.assertEqual(
            fill_default_hero_text('<h1>It works!</h1><p>      </p>'),
            f'<h1>It works!</h1><p>{DEFAULT_HERO_SUBTITLE_TEXT}</p>'
        )
