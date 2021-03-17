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
Integration tests - helper functions.
"""

import logging
import pathlib
import socket
import time

import requests

logger = logging.getLogger(__name__)


def get_url_contents(url, auth=None, attempts=10, delay=60, verify_ssl=True):
    """
    Connect to the given URL and returns its contents as a string.
    Does several attempts in case the first one failed.
    By default it verifies SSL certificates, but it can be disabled to be able to access external pages.

    Raises an exception if there is an HTTP error.
    """
    ca_path = str(pathlib.Path(__file__).parent / "certs" / "lets-encrypt-staging-ca.pem")
    total_attempts = attempts

    while True:
        try:
            if verify_ssl:
                res = requests.get(url, auth=auth, verify=ca_path)
            else:
                res = requests.get(url, auth=auth, verify=False)

            res.raise_for_status()
            return res.text
        except Exception:  # pylint: disable=broad-except
            logger.error('Attempt: %d - Unable to retrieve %s. ', total_attempts - attempts, url)
            if not attempts:
                raise
        time.sleep(delay)


def check_url_accessible(url, auth=None, attempts=10, delay=60):
    """
    Check that the given URL is accessible and that it returns a success status code.

    Raises an exception if there is an HTTP error.
    Returns nothing if connection was succesful.
    """
    get_url_contents(url, auth, attempts, delay)


def is_port_open(ip_addr, port):
    """
    Determine if the server at ip_addr is accepting connections on the given
    port or not.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return sock.connect_ex((ip_addr, port)) == 0
