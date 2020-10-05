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

SYNTHETICS_API_URL = 'https://synthetics.newrelic.com/synthetics/api/v3'

NEW_RELIC_API_BASE = 'https://api.newrelic.com/v2'
ALERTS_CHANNELS_API_URL = '{}/alerts_channels'.format(NEW_RELIC_API_BASE)
ALERTS_POLICIES_API_URL = '{}/alerts_policies'.format(NEW_RELIC_API_BASE)
ALERTS_POLICIES_CHANNELS_API_URL = '{}/alerts_policy_channels.json'.format(NEW_RELIC_API_BASE)
ALERTS_NRQL_CONDITIONS_API_URL = '{}/alerts_nrql_conditions'.format(NEW_RELIC_API_BASE)


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
        'options': {'verifySSL': True}, # SSL valid only for SIMPLE and BROWSER
    })
    r.raise_for_status()
    return r.headers['location'].rsplit('/', 1)[-1]


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
    url = '{}?policy_id={}&channel_ids={}'.format(
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
    )
    r.raise_for_status()


def add_alert_nrql_condition(policy_id, monitor_url, name):
    """
    Add a NRQL alert condition to the alert policy with the given id for the given URL.
    """
    url = '{}/policies/{}.json'.format(ALERTS_NRQL_CONDITIONS_API_URL, policy_id)
    logger.info('POST %s', url)
    query = "SELECT count(*) FROM SyntheticCheck WHERE monitorName = '{}' AND result = 'SUCCESS'".format(monitor_url)
    r = requests.post(
        url,
        headers=_request_headers(),
        json={
            'nrql_condition': {
                'type': 'static',
                'name': name,
                'enabled': True,
                'value_function': 'sum',
                'terms': [{
                    'duration': settings.NEWRELIC_NRQL_ALERT_CONDITION_DURATION,
                    'threshold': '1',
                    'operator': 'below',
                    'priority': 'critical',
                    'time_function': 'all',
                }],
                'nrql': {
                    'query': query,
                    'since_value': '3',
                }
            }
        }
    )
    r.raise_for_status()
    return r.json()['nrql_condition']['id']


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
            logger.info('Alert policy for %s has already been deleted. Proceeding.')
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


def delete_alert_nrql_condition(condition_id):
    """
    Delete the New Relic NRQL alerts alert condition with the given id.

    If the alert condition can't be found (DELETE request comes back with 404),
    treat it as if it has already been deleted; do not raise an exception in that case.
    """
    url = '{}/{}.json'.format(ALERTS_NRQL_CONDITIONS_API_URL, condition_id)
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
