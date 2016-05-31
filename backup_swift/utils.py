# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
Misc utils for backup_swift.
"""

# Imports #####################################################################

import contextlib
import logging
import requests

# Logging #####################################################################

logger = logging.getLogger(__name__)

# Functions #####################################################################


def ping_heartbeat_url(url):
    """
    Pings heartbeat url.

    :param str url: Url to ping
    :return: True if http request finished and returned proper status, False otherwise.
    """
    try:
        response = requests.get(url, timeout=30)
        return 200 <= response.status_code < 300
    except requests.RequestException:
        return False


@contextlib.contextmanager
def filter_logger(logger_name, new_filter):
    """
    Contextmanager to add a filter to a logger temporarily.
    :param str logger_name: Name of a logger to modify
    :param callable new_filter: Filter to add
    """
    changed_logger = logging.getLogger(logger_name)
    try:
        changed_logger.addFilter(new_filter)
        yield
    finally:
        changed_logger.removeFilter(new_filter)


def filter_swift(log_record):
    """
    Filters log records containing information about the fact that downloaded file was not modified.
    Swift backup spawns quite a log of these, which are not an error condition.
    """
    return '304 Not Modified' not in log_record.getMessage()
