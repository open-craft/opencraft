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
from enum import Enum
import itertools
import json
import logging
import selectors
import socket
import time
from typing import TYPE_CHECKING
from unittest.mock import Mock

from asgiref.sync import async_to_sync
import channels.layers
from dictdiffer import diff
import requests

if TYPE_CHECKING:
    from registration.models import BetaTestApplication  # pylint: disable=cyclic-import, useless-suppression

# Logging #####################################################################

logger = logging.getLogger(__name__)


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
        except Exception:  # pylint: disable=broad-except
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
        try:
            next_timeout = next(timeout)
        except StopIteration:
            logger.error('_line_timeout_generator returned (should never happen).'
                         'line_timeout: %s, global_timeout: %s',
                         line_timeout, global_timeout)
            next_timeout = 0
        available = selector.select(next_timeout)
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


def publish_data(data):
    """
    Publish the data to the 'ws' group.
    """
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)('ws', {'type': 'notification', 'message': data})


def build_instance_config_diff(instance_config: 'BetaTestApplication'):
    """
    Builds an configuration diff for the provided instance configuration.
    """
    instance = instance_config.instance
    original_config = {}
    new_config = {}
    for attr in ('instance_name', 'privacy_policy_url', 'public_contact_email'):
        original_config[attr] = getattr(instance, attr, None)
        new_config[attr] = getattr(instance_config, attr, None)

    if instance_config.draft_theme_config != instance.theme_config:
        original_config['theme_config'] = instance.theme_config
        new_config['theme_config'] = instance_config.draft_theme_config

    if instance_config.draft_static_content_overrides != instance.static_content_overrides:
        original_config['static_content_overrides'] = instance.static_content_overrides
        new_config['static_content_overrides'] = instance_config.draft_static_content_overrides

    return list(diff(original_config, new_config))


class DjangoChoiceEnum(Enum):
    """Enumeration that provides convenient methods for Django"""

    def __str__(self):
        return self.name

    @classmethod
    def choices(cls):
        """Render enum as tuple to use in Django choice field"""
        return tuple((prop.name, prop.value) for prop in cls)

    @classmethod
    def names(cls):
        """Return enum as list of string names """
        return list(prop.name for prop in cls)
