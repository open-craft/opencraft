# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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

import subprocess

from instance.tests.base import TestCase
from instance.utils import read_files


# Tests #######################################################################

class UtilsTestCase(TestCase):
    """
    Test cases for functions in the utils module
    """
    def test_read_files(self):
        """
        Ensure that the lines read are in the order they were written in each stream.
        """
        process = subprocess.Popen([
            "echo line1; echo line1 >&2; echo line2; echo line2 >&2; echo line3"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        lines = read_files(process.stdout, process.stderr)

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
