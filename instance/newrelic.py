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
New Relic API - Helper functions
"""

# Imports #####################################################################

import logging

from django.conf import settings
import requests


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Constants ###################################################################

SYNTHETICS_API_URL = 'https://synthetics.newrelic.com/synthetics/api/v1'


# Functions ###################################################################

def get_synthetics_monitors():
    """
    Return a list of active Synthetics monitors.
    """
    url = '{0}/monitors'.format(SYNTHETICS_API_URL)
    logger.info('GET %s', url)
    r = requests.get(url, headers=_request_headers())
    r.raise_for_status()
    return r.json()['monitors']


def create_synthetics_monitor(uri, name=None, monitor_type='SIMPLE',
                              frequency=5, locations=('AWS_US_EAST_1',)):
    """
    Create a monitor for the given uri and return its id.
    """
    url = '{0}/monitors'.format(SYNTHETICS_API_URL)
    logger.info('POST %s', url)
    r = requests.post(url, headers=_request_headers(), json={
        'name': uri,
        'uri': uri,
        'type': monitor_type,
        'frequency': frequency,
        'locations': locations,
        'status': 'ENABLED',
    })
    r.raise_for_status()
    return r.headers['location'].rsplit('/', 1)[-1]


def add_synthetics_email_alerts(monitor_id, emails):
    """
    Set up email alerts for the given monitor.
    """
    url = '{0}/monitors/{1}/notifications'.format(SYNTHETICS_API_URL,
                                                  monitor_id)
    logger.info('POST %s', url)
    r = requests.post(url, headers=_request_headers(), json={
        'count': len(emails),
        'emails': emails,
    })
    r.raise_for_status()


def delete_synthetics_monitor(monitor_id):
    """
    Delete the Synthetics monitor with the given id.
    """
    url = '{0}/monitors/{1}'.format(SYNTHETICS_API_URL, monitor_id)
    logger.info('DELETE %s', url)
    r = requests.delete(url, headers=_request_headers())
    r.raise_for_status()


def _request_headers():
    """
    Request headers for the New Relic API.
    """
    return {
        'X-Api-Key': settings.NEWRELIC_ADMIN_USER_API_KEY,
    }
