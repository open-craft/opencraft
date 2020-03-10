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
Theme schema tests
"""
import copy
import random

import ddt
from jsonschema import validate
from jsonschema.exceptions import ValidationError as JSONValidationError

from instance.tests.base import TestCase
from instance.schemas.theming import ref, theme_schema_v0, theme_schema_v1, theme_schema_validate


@ddt.ddt
class ThemeV0SchemaTestCase(TestCase):
    """
    Tests for the v0 theme schema.
    """
    def setUp(self):
        super().setUp()
        self.test_data = {
            'version': 0,
            'main_color': '#000',
            'link_color': '#111',
            'header_bg_color': '#222',
            'footer_bg_color': '#333'
        }

    def validate(self, value):
        """
        Validate the given value using the v0 schema.
        """
        validate(value, schema=theme_schema_v0)

    @ddt.data("", None, 1, False, [1, 2, 3, 4], "abcd")
    def test_invalid_data_types(self, value):
        """
        Test that validation fails when passing invalid data types for the value.
        """
        with self.assertRaisesRegex(JSONValidationError, "is not of type 'object'"):
            self.validate(value)

    @ddt.data(
        {},
        {'version': 0, 'main_color': '#000', "link_color": "#888"},
        {'version': 0, 'main_color': '#000', 'link_color': '#000', 'footer_bg_color': '#999'}
    )
    def test_missing_required_keys(self, value):
        """
        Test that the validation fails when the value is missing the required properties.
        """
        with self.assertRaisesRegex(JSONValidationError, "is a required property"):
            self.validate(value)

    @ddt.data(
        ([], "is not of type 'number'"),
        ({}, "is not of type 'number'"),
        ("a", "is not of type 'number'"),
        (-1, "is not one of"),
        (1, "is not one of"),
        (3.14, r"is not one of"),
    )
    @ddt.unpack
    def test_invalid_version(self, value, error_msg_regex):
        """
        Test that the validation fails when the value for "version" is invalid.
        """
        with self.assertRaisesRegex(JSONValidationError, error_msg_regex):
            self.test_data['version'] = value
            self.validate(self.test_data)

    @ddt.data(
        ('', 'does not match'),
        ([], "is not of type 'string'"),
        (12, "is not of type 'string'"),
        ({}, "is not of type 'string"),
        ('blue', 'does not match'),
        ('#ff', 'does not match'),
        ('#fffff', 'does not match'),
        ('#fffffff', 'does not match'),
    )
    @ddt.unpack
    def test_invalid_color_values(self, value, error_msg_regex):
        """
        Test that the validation fails when an invalid value is given for a color
        """
        for key, val in theme_schema_v0['properties'].items():
            if val == ref('color'):
                with self.assertRaisesRegex(JSONValidationError, error_msg_regex):
                    self.test_data[key] = value
                    self.validate(self.test_data)
                    self.test_data[key] = val

    def test_valid_value(self):
        """
        Test that the validation succeeds when a valid value is given.
        """
        self.validate(self.test_data)


@ddt.ddt
class ThemeV1SchemaTestCase(TestCase):
    """
    Tests for the theme_config v1 schema.
    """
    def setUp(self):
        super().setUp()
        self.schema = copy.deepcopy(theme_schema_v1)

    def validate(self, value, schema=None):
        """
        Validate the given value using the optionally given schema or self.schema.
        """
        validate(value, schema=schema if schema else self.schema)

    @ddt.data("", None, 1, False, [1, 2, 3, 4], "abcd")
    def test_invalid_data_types(self, value):
        """
        Test that validation fails when passing invalid data types for the value.
        """
        with self.assertRaisesRegex(JSONValidationError, "is not of type 'object'"):
            self.validate(value)

    @ddt.data(
        ([], "is not of type 'number'"),
        ({}, "is not of type 'number'"),
        ("a", "is not of type 'number'"),
        (-1, "is not one of"),
        (0, "is not one of"),
        (3.14, "is not one of"),
    )
    @ddt.unpack
    def test_invalid_version(self, value, error_msg_regex):
        """
        Test that the validation fails when the value for "version" is invalid.
        """
        with self.assertRaisesRegex(JSONValidationError, error_msg_regex):
            self.validate({"version": value})

    @ddt.data(
        ('', 'does not match'),
        ([], "is not of type 'string'"),
        (12, "is not of type 'string'"),
        ({}, "is not of type 'string"),
        ('blue', 'does not match'),
        ('#ff', 'does not match'),
        ('#fffff', 'does not match'),
        ('#fffffff', 'does not match'),
    )
    @ddt.unpack
    def test_invalid_color_values(self, value, error_msg_regex):
        """
        Test that the validation fails when an invalid value is given for a color.
        """
        del self.schema['required']
        for key, val in self.schema['properties'].items():
            if val == ref('color'):
                with self.assertRaisesRegex(JSONValidationError, error_msg_regex):
                    self.validate({key: value})

    @ddt.data('', [], 12, {}, 'blue', '#ff', '#fffff', '#fffffff')
    def test_invalid_flag_value(self, value):
        """
        Test that the validation fails when an invalid value is given for a flag.
        """
        del self.schema['required']
        del self.schema['dependencies']
        for key, val in self.schema['properties'].items():
            if val == ref('flag'):
                with self.assertRaisesRegex(JSONValidationError, 'is not one of'):
                    self.validate({key: value})

    def test_flag_dependencies(self):
        """
        Test that the validation fails when dependencies are missing.
        """
        for key, val in self.schema['properties'].items():
            if val == ref('flag'):
                dependencies = self.schema['dependencies'][key]
                with self.assertRaisesRegex(JSONValidationError, 'is a dependency'):
                    self.validate({key: True})
                    for i in range(1, len(dependencies)):
                        data = {key: True}
                        data.update({k: '#fff' for k in random.sample(dependencies, i)})
                        self.validate(data)

    def test_additional_property(self):
        """
        Test that the validation fails when an unknown additional property is given.
        """
        del self.schema['required']
        with self.assertRaisesRegex(JSONValidationError, 'Additional properties are not allowed'):
            self.validate({'foo': 'bar'})


@ddt.ddt
class ThemeConfigValidationTestCase(TestCase):
    """
    Tests for theme config validation.
    """
    @ddt.data("", 1, False, [1, 2, 3, 4], "abcd")
    def test_invalid_data_types(self, value):
        """
        Test that validation fails when passing invalid data types for the value.
        """
        with self.assertRaisesRegex(JSONValidationError, "is not of type"):
            theme_schema_validate(value)

    def test_null_accepted(self):
        """
        Test that an empty object is accepted as valid.
        """
        theme_schema_validate(None)

    def test_data_in_v0_and_v1_schema_accepted(self):
        """
        Test that the data validating against the v0 or v1 schema is accepted.
        """
        theme_schema_validate({'version': 1, 'main-color': '#fff', 'link-color': '#000'})
        theme_schema_validate({
            'version': 0,
            'main_color': '#000',
            'link_color': '#111',
            'header_bg_color': '#222',
            'footer_bg_color': '#333'
        })

    def test_invalid_v0_schema_data_causes_validation_failure(self):
        """
        Test that the schema validation for the v0 schema works even in the combined schema.
        """
        with self.assertRaises(JSONValidationError):
            theme_schema_validate({
                'version': 0,
                'main_color': 'red',
                'link_color': '#fff',
                'header_bg_color': '#fff',
                'footer_bg_color': '#fff'
            })

    @ddt.data(
        {'main-color': 'red'},
        {'main-color': 1},
        {'customize-login-btn': 'true'},
        {'customize-login-btn': 1}
    )
    def test_invalid_v1_schema_data_causes_validation_failure(self, value):
        """
        Test that the schema validation for the v1 schema works even in the combined schema.
        """
        value['version'] = 1
        with self.assertRaises(JSONValidationError):
            theme_schema_validate(value)
