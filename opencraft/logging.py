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
OpenCraft - Logging
"""

# Imports #####################################################################

import os
import gzip
from logging.handlers import RotatingFileHandler


# Handlers ####################################################################

class GzipRotatingFileHandler(RotatingFileHandler):
    """
    Uses gzip to compress the rotated log files.

    https://docs.python.org/3/howto/logging-cookbook.html#using-a-rotator-and-namer-to-customize-log-rotation-processing
    """

    def __init__(self, *args, **kwargs):
        super(GzipRotatingFileHandler, self).__init__(*args, **kwargs)
        self.namer = self._namer
        self.rotator = self._rotator

    @staticmethod
    def _namer(name):
        """Append a .gz suffix to the rotated files."""
        return name + '.gz'

    @staticmethod
    def _rotator(source, dest):
        """Write compressed output when rotating files."""
        with open(source, "rb") as sf:
            with gzip.open(dest, "wb", compresslevel=9) as df:
                for line in sf:
                    df.write(line)
            os.remove(source)
