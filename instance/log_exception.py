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
Facilities to log uncaught exceptions, ensuring it is properly propagated to the client
"""

# Imports #####################################################################

import traceback

from functools import wraps


# Functions ###################################################################

def log_exception(method):
    """
    Decorator to log uncaught exceptions on methods
    Uses the object logging facilities, ie the following method should be defined:
    self.log(<log_level_str>, <log_message>)`
    """
    @wraps(method)
    def wrapper(self, *args, **kwds): #pylint: disable=missing-docstring
        try:
            return method(self, *args, **kwds)
        except:
            self.log('exception', traceback.format_exc())
            raise
    return wrapper
