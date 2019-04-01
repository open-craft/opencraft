# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
Instance app - Util functions
"""

# Imports #####################################################################

import itertools
import json
import selectors
import socket
import time
from unittest.mock import Mock

import requests


# Functions ###################################################################

def is_port_open(ip, port):
    """
    Check if the port is open on the provided ip
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return sock.connect_ex((ip, port)) == 0


def to_json(obj):
    """
    Convert an object to a JSON string
    """
    def dumper(obj2):
        """
        Serializer that avoids throwing exceptions on objects it can't serialize
        """
        if isinstance(obj2, Mock):
            return repr(obj2)
        try:
            return obj2.toJSON()
        except: #pylint: disable=bare-except
            return repr(obj2)

    if not hasattr(obj, 'toJSON'):
        obj = obj.__dict__
    return json.dumps(obj, sort_keys=True, indent=4, default=dumper)


def get_requests_retry(total=10, connect=10, read=10, redirect=10, backoff_factor=0,
                       status_forcelist=range(500, 600)):
    """
    Returns a urllib3 `Retry` object, with the default requests retry policy
    """
    return requests.packages.urllib3.util.retry.Retry(
        total=total,
        connect=connect,
        read=read,
        redirect=redirect,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )


def _line_timeout_generator(line_timeout, global_timeout):
    """
    Helper function for poll_streams() to compute the timeout for a single line.
    """
    if global_timeout is not None:
        deadline = time.time() + global_timeout
        while True:
            global_timeout = deadline - time.time()
            if line_timeout is not None:
                yield min(line_timeout, global_timeout)
            else:
                yield global_timeout
    else:
        yield from itertools.repeat(line_timeout)


def poll_streams(*files, line_timeout=None, global_timeout=None):
    """
    Poll a set of file objects for new data and return it line by line.

    The file objects should be line-buffered or unbuffered.  Regular files won't
    work on some systems (notably Linux, where DefaultSelector uses epoll() by
    default; this function is pointless for regular files anyway, since they are
    always ready for reading and writing).

    Each line returned is a 2-items tuple, with the first item being the object
    implementing the file interface, and the second the text read.

    The optional parameters line_timeout and global_timeout specify how long in
    seconds to wait at most for a single line or for all lines.  If no timeout
    is specified, this function will block indefintely for each line.
    """
    selector = selectors.DefaultSelector()
    for fileobj in files:
        selector.register(fileobj, selectors.EVENT_READ)
    timeout = _line_timeout_generator(line_timeout, global_timeout)
    while selector.get_map():
        available = selector.select(next(timeout))
        if not available:
            # TODO(smarnach): This can also mean that the process received a signal.
            raise TimeoutError('Could not read line before timeout: {timeout}'.format(timeout=timeout))
        for key, unused_mask in available:
            line = key.fileobj.readline()
            if line:
                yield (key.fileobj, line)
            else:
                selector.unregister(key.fileobj)


def sufficient_time_passed(earlier_date, later_date, expected_days_since):
    """
    Check if at least `expected_days_since` have passed between `earlier_date`
    and `later_date`.
    """
    days_passed = (later_date - earlier_date).days
    return days_passed >= expected_days_since
