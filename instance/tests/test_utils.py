# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
Utils module - Tests
"""

# Imports #####################################################################

from datetime import datetime
import itertools
import subprocess
from unittest.mock import patch

from instance.tests.base import TestCase
from instance.utils import sufficient_time_passed, poll_streams, _line_timeout_generator, to_json


# Tests #######################################################################

class UtilsTestCase(TestCase):
    """
    Test cases for functions in the utils module
    """
    def test_poll_streams(self):
        """
        Ensure that the lines read are in the order they were written in each stream.
        """
        process = subprocess.Popen([
            "echo line1; echo line1 >&2; echo line2; echo line2 >&2; echo line3"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        lines = poll_streams(process.stdout, process.stderr)

        expected = [
            (process.stdout, b"line1\n"),
            (process.stderr, b"line1\n"),
            (process.stdout, b"line2\n"),
            (process.stderr, b"line2\n"),
            (process.stdout, b"line3\n"),
        ]

        def key(entry):
            """
            Helper function used together with sorting routines in order to
            identify which attribute to sort by.
            """
            return entry[0].fileno()

        self.assertEqual(sorted(lines, key=key), sorted(expected, key=key))

    @patch('time.time')
    def test_line_timeout_generator(self, mock_time):
        """
        Test the helper function to generate timeouts for poll_streams().
        """
        # Test with global timeout set
        mock_time.side_effect = itertools.count().__next__
        timeout = _line_timeout_generator(3, 6)
        for actual, expected in zip(timeout, [3, 3, 3, 2, 1, 0]):
            self.assertEqual(actual, expected)

        # Test without global timeout
        timeout = _line_timeout_generator(3, None)
        mock_time.reset_mock()
        for actual, expected in zip(timeout, [3, 3, 3, 3, 3, 3]):
            self.assertEqual(actual, expected)
        self.assertFalse(mock_time.called)

    def test_sufficient_time_passed(self):
        """
        Test helper function for checking if sufficient time passed between two dates.
        """
        date = datetime(2016, 9, 25, 8, 20, 5)
        reference_date = datetime(2016, 10, 11, 15, 10, 30)

        # Delta between dates greater than expected delta (actual delta: 16 days)
        result = sufficient_time_passed(date, reference_date, 5)
        self.assertTrue(result)
        # Delta between dates equal to expected delta
        result = sufficient_time_passed(date, reference_date, 16)
        self.assertTrue(result)
        # Delta between dates less than expected delta (actual delta: 16 days)
        result = sufficient_time_passed(date, reference_date, 20)
        self.assertFalse(result)
        # Negative delta (reference date follows date), delta between dates greater than expected delta
        result = sufficient_time_passed(reference_date, date, 5)
        self.assertFalse(result)
        # Negative delta (reference date follows date), delta between dates less than expected delta
        result = sufficient_time_passed(reference_date, date, 20)
        self.assertFalse(result)

    def test_to_json(self):
        """
        Test the to_json() helper function.
        """
        class Serializable:
            """
            A test class with a toJSON() method.
            """
            def toJSON(self):  # nopep8 pylint: disable=invalid-name
                """
                Fake JSON serialization.
                """
                return vars(self)

        class NonSerializable:
            """
            A test class without a toJSON() method.
            """
        serializable = Serializable()
        self.assertEqual(to_json(serializable), '{}')
        non_serializable = NonSerializable()
        non_serializable.attr = 42  # pylint: disable=attribute-defined-outside-init
        self.assertEqual(to_json(non_serializable), '{\n    "attr": 42\n}')
        serializable.attr = non_serializable  # pylint: disable=attribute-defined-outside-init
        self.assertEqual(to_json(serializable), '{\n    "attr": "%s"\n}' % (non_serializable,))
