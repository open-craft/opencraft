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
Instance app - Util functions
"""

# Imports #####################################################################

import json
import requests
import select
import socket

from mock import Mock


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


def get_requests_retry(total=10, connect=10, read=10, redirect=10, backoff_factor=0.5):
    """
    Returns a urllib3 `Retry` object, with the default requests retry policy
    """
    return requests.packages.urllib3.util.retry.Retry(
        total=total,
        connect=connect,
        read=read,
        redirect=redirect,
        backoff_factor=backoff_factor
    )


def read_files(*fds):
    """
    Given a list of objects implementing the file interface, poll them for new
    data and yield the lines read as they are written.

    Each line returned is a 2-items tuple, with the first item being the object
    implementing the file interface, and the second the text read.
    """
    poll = select.poll()
    fd_map = {}
    for fd in fds:
        poll.register(fd.fileno(), select.POLLIN)
        fd_map[fd.fileno()] = fd
    while fd_map:
        available = poll.poll()
        for entry in available:
            fileno = entry[0]
            line = fd_map[fileno].readline()
            if line:
                yield (fd_map[fileno], line)
            else:
                poll.unregister(fileno)
                del fd_map[fileno]
