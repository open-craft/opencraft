# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
#
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
# Copyright (C) 2015 RedHat - Author: Loic Dachary <loic@dachary.org>
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
import os
import socket
import subprocess

from mock import Mock


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Functions ###################################################################

def is_port_open(ip, port):
    """
    Check if the port is open on the provided ip
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return sock.connect_ex((ip, port)) == 0


def sh(command, env=None): #pylint: disable=invalid-name
    """
    Run the shell command and return the output in ascii (stderr and
    stdout).  If the command fails, raise an exception. The command
    and its output are logged, on success and on error.
    """
    logger.debug('Running "%s" with env %s', command, env)

    sub_env = os.environ.copy()
    if env:
        sub_env.update(env)

    output = ''
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT,
                                         shell=True)
    except subprocess.CalledProcessError as e:
        logger.exception(command + " error " + str(e.output))
        raise e
    logger.debug(command + " output " + str(output))
    return output.decode('utf-8')


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
