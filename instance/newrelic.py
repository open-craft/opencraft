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

def get_synthetics_monitor(monitor_id):
    """
    Return details of an active Synthetics monitor.

    Example return value:
        {
            "id": UUID,
            "name": string,
            "type": string,
            "frequency": integer,
            "uri": string,
            "locations": array of strings,
            "status": string,
            "slaThreshold": double,
            "userId": integer,
            "apiVersion": string
        }
    """
    url = '{0}/monitors/{1}'.format(SYNTHETICS_API_URL, monitor_id)
    logger.info('GET %s', url)
    r = requests.get(url, headers=_request_headers())
    r.raise_for_status()
    return r.json()


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


def get_synthetics_notification_emails(monitor_id):
    """
    Get the list of emails that New Relic will notify when the monitor
    detects that the URI is offline.
    """
    url = '{0}/monitors/{1}/notifications'.format(SYNTHETICS_API_URL,
                                                  monitor_id)
    logger.info('GET %s', url)
    r = requests.get(url, headers=_request_headers())
    r.raise_for_status()
    return r.json()['emails']


def add_synthetics_email_alerts(monitor_id, emails):
    """
    Add email addresses to the notification list for the given monitor.

    Will raise an error if the email is already on the list.
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

    If the monitor can't be found (DELETE request comes back with 404),
    treat it as if it has already been deleted; do not raise an exception in that case.
    """
    url = '{0}/monitors/{1}'.format(SYNTHETICS_API_URL, monitor_id)
    logger.info('DELETE %s', url)
    try:
        r = requests.delete(url, headers=_request_headers())
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        if r.status_code == requests.codes.not_found:
            logger.info('Monitor for %s has already been deleted. Proceeding.')
        else:
            raise


def _request_headers():
    """
    Request headers for the New Relic API.
    """
    return {
        'X-Api-Key': settings.NEWRELIC_ADMIN_USER_API_KEY,
    }
