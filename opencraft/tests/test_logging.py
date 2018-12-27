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
OpenCraft - Logging - Tests
"""

# Imports #####################################################################

import os
import sys
import gzip
import logging
import tempfile
import shutil

from instance.tests.base import TestCase
from opencraft.logging import GzipRotatingFileHandler


# Tests #######################################################################

class GzipRotatingFileHandlerTest(TestCase):
    """
    Test cases for the compressing log file handler.
    """

    def setUp(self):
        super(GzipRotatingFileHandlerTest, self).setUp()

        # Create temp log dir, to be deleted on cleanup
        self.log_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.log_dir)

        # Configure log handler
        self.log_file = os.path.join(self.log_dir, 'test.log')
        self.num_logs = 3
        self.test_string = 'a' * 1000
        self.max_bytes = sys.getsizeof(self.test_string) + 1
        self.rotated_log_files = [
            '{log_file}.{idx}.{suffix}'.format(log_file=self.log_file, idx=idx + 1, suffix='gz')
            for idx in range(self.num_logs)
        ]

        # Log to this handler only
        self.logger = logging.getLogger('test')
        for handler in list(self.logger.handlers):
            self.logger.removeHandler(handler)
        self.logger.addHandler(GzipRotatingFileHandler(backupCount=self.num_logs,
                                                       filename=self.log_file,
                                                       maxBytes=self.max_bytes))

    def test_namer(self):
        """
        Ensure the rotated log files are named correctly.
        """
        # Initially, only the base log file exists
        self.assertTrue(os.path.isfile(self.log_file))
        for log_file in self.rotated_log_files:
            self.assertFalse(os.path.isfile(log_file))

        # As messages are logged, the rotated log files get created
        for idx in range(self.num_logs + 1):
            self.logger.error(self.test_string)
            self.assertTrue(os.path.isfile(self.log_file))

            for log_file in self.rotated_log_files[:idx]:
                self.assertTrue(os.path.isfile(log_file))

            for log_file in self.rotated_log_files[idx:]:
                self.assertFalse(os.path.isfile(log_file))

    def test_rotator(self):
        """
        Ensure the rotated log files are compressed.
        """
        self.logger.error(self.test_string)
        for log_file in self.rotated_log_files:
            self.logger.error(self.test_string)
            with gzip.open(log_file, 'rt') as gz:
                data = gz.read().strip()
                self.assertEqual(self.test_string, data)
