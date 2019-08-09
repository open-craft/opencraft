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
New Relic API - Helper functions
"""

# Imports #####################################################################

import logging

import requests
from django.conf import settings

# Logging #####################################################################

logger = logging.getLogger(__name__)


# Constants ###################################################################

SYNTHETICS_API_URL = 'https://synthetics.newrelic.com/synthetics/api/v1'

NEW_RELIC_API_BASE = 'https://api.newrelic.com/v2'
ALERTS_CHANNELS_API_URL = '{}/alerts_channels'.format(NEW_RELIC_API_BASE)
ALERTS_POLICIES_API_URL = '{}/alerts_policies'.format(NEW_RELIC_API_BASE)
ALERTS_POLICIES_CHANNELS_API_URL = '{}/alerts_policy_channels.json'.format(NEW_RELIC_API_BASE)
ALERTS_CONDITIONS_API_URL = '{}/alerts_synthetics_conditions'.format(NEW_RELIC_API_BASE)


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


def add_alert_policy(name, incident_preference='PER_POLICY'):
    """
    Create an alert policy with the given name and the given incident preference and return the policy id.
    """
    url = '{}.json'.format(ALERTS_POLICIES_API_URL)
    logger.info('POST %s', url)
    r = requests.post(
        url,
        headers=_request_headers(),
        json={"policy": {"incident_preference": incident_preference, "name": name}}
    )
    r.raise_for_status()
    return r.json()['policy']['id']


def add_email_notification_channel(email_address):
    """
    Create an email notification channel with the given email address and return the channel id.
    """
    url = '{}.json'.format(ALERTS_CHANNELS_API_URL)
    logger.info('POST %s', url)
    r = requests.post(
        url,
        headers=_request_headers(),
        json={
            'channel': {
                'name': email_address,
                'type': 'email',
                'configuration': {
                    'recipients': email_address,
                    'include_json_attachment': False
                }
            }
        }
    )
    r.raise_for_status()
    return r.json()["channels"][0]["id"]


def add_notification_channels_to_policy(policy_id, channel_ids):
    """
    Update the notification channels for the given policy id with the notification channels corresponding
    to the given channel ids.
    """
    url = '{0}?policy_id={1}&channel_ids={0}'.format(
        ALERTS_POLICIES_CHANNELS_API_URL,
        policy_id,
        ','.join([str(id) for id in channel_ids])
    )
    logger.info('PUT %s', url)

    # This API call only appends to the existing notification channels and ignores the duplicates.
    headers = _request_headers()
    headers['Content-Type'] = 'application/json'
    r = requests.put(
        url,
        headers=headers,
        json=""
    )
    r.raise_for_status()


def add_alert_condition(policy_id, monitor_id, name):
    """
    Add an alert condition to the alert policy with the given id for the monitor with the given id.
    """
    url = '{0}/policies/{1}.json'.format(ALERTS_CONDITIONS_API_URL, policy_id)
    logger.info('POST %s', url)
    r = requests.post(
        url,
        headers=_request_headers(),
        json={
            'synthetics_condition': {
                'name': name,
                'monitor_id': monitor_id,
                'enabled': True
            }
        }
    )
    r.raise_for_status()
    return r.json()['synthetics_condition']['id']


def delete_alert_policy(policy_id):
    """
    Delete the New Relic alerts alert policy with the given id.
    """
    url = '{}/{}.json'.format(ALERTS_POLICIES_API_URL, policy_id)
    logger.info('DELETE %s', url)
    try:
        r = requests.delete(url, headers=_request_headers())
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        if r.status_code == requests.codes.not_found:
            logger.info('Alert condition for %s has already been deleted. Proceeding.')
        else:
            raise


def delete_email_notification_channel(channel_id):
    """
    Delete the New Relic email notification channel with the given id.

    If the email notification channel can't be found, treat it as if it has already been deleted
    and do not raise an exception in that case.
    """
    url = '{}/{}.json'.format(ALERTS_CHANNELS_API_URL, channel_id)
    logger.info('DELETE %s', url)
    try:
        r = requests.delete(url, headers=_request_headers())
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        if r.status_code == requests.codes.not_found:
            logger.info('Email notification channel for %s has already been deleted. Proceeding.')
        else:
            raise


def delete_alert_condition(condition_id):
    """
    Delete the New Relic alerts alert condition with the given id.

    If the alert condition can't be found (DELETE request comes back with 404),
    treat it as if it has already been deleted; do not raise an exception in that case.
    """
    url = '{}/{}.json'.format(ALERTS_CONDITIONS_API_URL, condition_id)
    logger.info('DELETE %s', url)
    try:
        r = requests.delete(url, headers=_request_headers())
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        if r.status_code == requests.codes.not_found:
            logger.info('Alert condition for %s has already been deleted. Proceeding.')
        else:
            raise


def _request_headers():
    """
    Request headers for the New Relic API.
    """
    return {
        'X-Api-Key': settings.NEWRELIC_ADMIN_USER_API_KEY,
    }
