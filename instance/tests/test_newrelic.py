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
New Relic - Tests
"""

# Imports #####################################################################

import json

from django.test import override_settings
import requests
import responses

from instance import newrelic
from instance.tests.base import TestCase


# Tests #######################################################################

@override_settings(NEWRELIC_ADMIN_USER_API_KEY='admin-api-key')
class NewRelicTestCase(TestCase):
    """
    Test cases for New Relic helper functions & API calls
    """
    @responses.activate
    def test_get_synthetics_monitor(self):
        """
        Check that the get_synthetics_monitor function fetches the details
        of a specific monitor from the Synthetics API.
        """
        monitor_id = 'd35c6c1c-23a5-4a67-b3b0-287c34e84664'
        response_json = {
            'apiVersion': '0.2.2',
            'createdAt': '2016-06-06T07:11:51.859+0000',
            'frequency': 5,
            'id': monitor_id,
            'locations': ['AWS_US_EAST_1'],
            'modifiedAt': '2016-06-06T07:11:51.859+0000',
            'name': 'test-simple',
            'slaThreshold': 7.0,
            'status': 'ENABLED',
            'type': 'SIMPLE',
            'uri': 'http://newrelic-test.stage.opencraft.hosting/',
            'userId': 0,
        }
        responses.add(responses.GET,
                      '{0}/monitors/{1}'.format(newrelic.SYNTHETICS_API_URL, monitor_id),
                      json=response_json, status=200)
        self.assertEqual(newrelic.get_synthetics_monitor(monitor_id), response_json)
        self.assertEqual(len(responses.calls), 1)
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')

    @responses.activate
    def test_create_synthetics_monitor(self):
        """
        Check that the create_synthetics_monitor function creates a monitor
        and returns its id.
        """
        monitor_id = '924a289a-6997-41ba-92be-bbe497b49753'
        monitor_url = '{0}/monitors/{1}'.format(newrelic.SYNTHETICS_API_URL,
                                                monitor_id)
        responses.add(responses.POST,
                      '{0}/monitors'.format(newrelic.SYNTHETICS_API_URL),
                      adding_headers={'Location': monitor_url}, status=201)
        url = 'http://newrelic-test.stage.opencraft.hosting/'
        self.assertEqual(newrelic.create_synthetics_monitor(url), monitor_id)
        self.assertEqual(len(responses.calls), 1)
        request_json = json.loads(responses.calls[0].request.body.decode())
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')
        self.assertEqual(request_json, {
            'name': url,
            'uri': url,
            'type': 'SIMPLE',
            'frequency': 5,
            'locations': ['AWS_US_EAST_1'],
            'status': 'ENABLED',
            # 'options': {'verifySSL': True},
        })

    @responses.activate
    def test_create_synthetics_ssl_monitor(self):
        """
        Check that the create_synthetics_ssl_monitor function creates an ssl monitor
        and returns its id.
        """
        monitor_id = '683a16bd-fe4b-4a54-9925-8d90371ffa45'
        monitor_url = '{0}/monitors/{1}'.format(newrelic.SYNTHETICS_API_URL,
                                                monitor_id)
        responses.add(responses.POST,
                      '{0}/monitors'.format(newrelic.SYNTHETICS_API_URL),
                      adding_headers={'Location': monitor_url}, status=201)
        url = 'http://newrelic-test.stage.opencraft.hosting/'
        self.assertEqual(newrelic.create_synthetics_ssl_monitor(url), monitor_id)
        self.assertEqual(len(responses.calls), 1)
        request_json = json.loads(responses.calls[0].request.body.decode())
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')
        self.assertEqual(request_json, {
            'name': url,
            'type': 'SCRIPT_API',
            'frequency': 1440,
            'locations': ['AWS_US_EAST_1'],
            'status': 'ENABLED',
        })

    @responses.activate
    def test_update_synthetics_ssl_monitor(self):
        """
        Check that update_synthetics_ssl_monitor updates the script of the monitor
        """
        monitor_id = '683a16bd-fe4b-4a54-9925-8d90371ffa45'
        monitor_url = '{0}/monitors/{1}/script'.format(newrelic.SYNTHETICS_API_URL,
                                                       monitor_id)
        responses.add(responses.PUT,
                      '{0}/monitors/{1}/script'.format(newrelic.SYNTHETICS_API_URL, monitor_id),
                      adding_headers={'Location': monitor_url}, status=201)
        url = 'https://newrelic-test.stage.opencraft.hosting/'
        newrelic.update_synthetics_ssl_monitor(monitor_id, url)
        self.assertEqual(len(responses.calls), 1)
        request_json = json.loads(responses.calls[0].request.body.decode())
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')
        self.assertIn('scriptText', request_json)

    @responses.activate
    def test_get_synthetics_notification_emails(self):
        """
        Check that the get_synthetics_notification_emails function gets a list of
        email addresses receiving alerts for the specified monitor.
        """
        monitor_id = '924a289a-6997-41ba-92be-bbe497b49753'
        emails = ['foo@example.com', 'bar@example.com']
        response_json = {
            'count': 2,
            'emails': emails,
        }
        responses.add(responses.GET,
                      '{0}/monitors/{1}/notifications'.format(newrelic.SYNTHETICS_API_URL, monitor_id),
                      json=response_json, status=200)
        self.assertEqual(newrelic.get_synthetics_notification_emails(monitor_id), emails)

    @responses.activate
    def test_add_synthetics_email_alerts(self):
        """
        Check that the add_synthetics_email_alerts function adds email alerts.
        """
        monitor_id = '924a289a-6997-41ba-92be-bbe497b49753'
        monitor_url = '{0}/monitors/{1}'.format(newrelic.SYNTHETICS_API_URL,
                                                monitor_id)
        responses.add(responses.POST,
                      '{0}/notifications'.format(monitor_url),
                      status=204)
        emails = ['foo@example.com', 'bar@example.com']
        newrelic.add_synthetics_email_alerts(monitor_id, emails)
        self.assertEqual(len(responses.calls), 1)
        request_json = json.loads(responses.calls[0].request.body.decode())
        self.assertEqual(request_json, {
            'count': len(emails),
            'emails': emails,
        })

    @responses.activate
    def test_delete_synthetics_monitor(self):
        """
        Check that the delete_synthetics_monitor function deletes the monitor
        with the given id.
        """
        monitor_id = '3e442fa8-ec6c-4bf7-94ac-a0eccb817587'
        responses.add(responses.DELETE,
                      '{0}/monitors/{1}'.format(newrelic.SYNTHETICS_API_URL,
                                                monitor_id),
                      status=204)
        newrelic.delete_synthetics_monitor(monitor_id)
        self.assertEqual(len(responses.calls), 1)
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')

    def test_delete_synthetics_monitor_exceptions(self):
        """
        Check that the delete_synthetics_monitor function behaves correctly if DELETE request unsuccessful.

        We expect the function *not* to raise an exception if the monitor to delete
        can not be found (i.e., if the DELETE request comes back with a 404).

        In all other cases the function should raise an exception.
        """
        monitor_id = '2085b3d6-3689-4847-97cc-f7c91d86cd1d'

        client_errors = [status_code for status_code in requests.status_codes._codes if 400 <= status_code < 500]
        server_errors = [status_code for status_code in requests.status_codes._codes if 500 <= status_code < 600]

        for error in client_errors + server_errors:
            with responses.RequestsMock() as mock_responses:
                mock_responses.add(responses.DELETE,
                                   '{0}/monitors/{1}'.format(newrelic.SYNTHETICS_API_URL,
                                                             monitor_id),
                                   status=error)
                try:
                    newrelic.delete_synthetics_monitor(monitor_id)
                except requests.exceptions.HTTPError:
                    if error == requests.codes.not_found:
                        self.fail('Should not raise an exception for {} response.'.format(error))
                else:
                    if not error == requests.codes.not_found:
                        self.fail('Should raise an exception for {} response.'.format(error))

    @responses.activate
    def test_add_alert_policy(self):
        """
        Check that the add_alert_policy function adds an alert
        """
        url = '{}.json'.format(newrelic.ALERTS_POLICIES_API_URL)
        policy_name = 'Test'
        policy_id = 1
        response_json = {
            'policy': {
                'id': policy_id
            }
        }
        responses.add(responses.POST, url, json=response_json, status=201)
        self.assertEqual(newrelic.add_alert_policy(policy_name), policy_id)
        self.assertEqual(len(responses.calls), 1)
        request_json = json.loads(responses.calls[0].request.body.decode())
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')
        self.assertEqual(request_json, {
            'policy': {
                'incident_preference': 'PER_POLICY',
                'name': policy_name
            }
        })

    @responses.activate
    def test_add_email_notification_channel(self):
        """
        Check that the add_email_notification_channel function adds a notification channel.
        """
        url = '{}.json'.format(newrelic.ALERTS_CHANNELS_API_URL)
        email_address = 'test@example.com'
        channel_id = 1
        response_json = {
            'channels': [
                {
                    'id': channel_id
                }
            ]
        }
        responses.add(responses.POST, url, json=response_json, status=201)
        self.assertEqual(newrelic.add_email_notification_channel(email_address), channel_id)
        self.assertEqual(len(responses.calls), 1)
        request_json = json.loads(responses.calls[0].request.body.decode())
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')
        self.assertEqual(request_json, {
            'channel': {
                'name': email_address,
                'type': 'email',
                'configuration': {
                    'recipients': email_address,
                    'include_json_attachment': False
                }
            }
        })

    @responses.activate
    def test_add_notification_channels_to_policy(self):
        """
        Check that the add_notification_channels_to_policy function adds the given notification channels to
        the given policy.
        """
        policy_id = 1
        channel_ids = ['10', '11']
        url = '{}?policy_id={}&channel_ids={}'.format(
            newrelic.ALERTS_POLICIES_CHANNELS_API_URL,
            policy_id,
            ','.join(channel_ids)
        )
        responses.add(responses.PUT, url, json='', status=200)
        newrelic.add_notification_channels_to_policy(policy_id, channel_ids)
        self.assertEqual(len(responses.calls), 1)
        request_body = responses.calls[0].request.body
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')
        self.assertEqual(request_body, None)

    @responses.activate
    def test_add_alert_condition(self):
        """
        Check that the add_alert_condition function adds an alert condition for the given monitor to
        the given alert policy
        """
        policy_id = 1
        monitor_id = 'abcde-fghij-klmno-12345'
        synthetics_condition_id = 1
        condition_name = 'Test'
        url = '{}/policies/{}.json'.format(newrelic.ALERTS_CONDITIONS_API_URL, policy_id)
        responses.add(
            responses.POST,
            url,
            json={'synthetics_condition': {'id': synthetics_condition_id}},
            status=201
        )
        self.assertEqual(newrelic.add_alert_condition(policy_id, monitor_id, condition_name), synthetics_condition_id)
        self.assertEqual(len(responses.calls), 1)
        request_json = json.loads(responses.calls[0].request.body.decode())
        request_headers = responses.calls[0].request.headers
        self.assertEqual(request_headers['x-api-key'], 'admin-api-key')
        self.assertEqual(request_json, {
            'synthetics_condition': {
                'name': condition_name,
                'monitor_id': monitor_id,
                'enabled': True
            }
        })

    @responses.activate
    def test_delete_alert_policy(self):
        """
        Check that the delete_alert_policy function behaves correctly if DELETE request unsuccessful.

        We expect the function *not* to raise an exception if the alert policy to delete
        can not be found (i.e., if the DELETE request comes back with a 404).

        In all other cases the function should raise an exception.
        """
        policy_id = 1

        client_errors = [status_code for status_code in requests.status_codes._codes if 400 <= status_code < 500]
        server_errors = [status_code for status_code in requests.status_codes._codes if 500 <= status_code < 600]

        for error in client_errors + server_errors:
            with responses.RequestsMock() as mock_responses:
                mock_responses.add(
                    responses.DELETE,
                    '{}/{}.json'.format(newrelic.ALERTS_POLICIES_API_URL, policy_id),
                    status=error
                )
                try:
                    newrelic.delete_alert_policy(policy_id)
                except requests.exceptions.HTTPError:
                    if error == requests.codes.not_found:
                        self.fail('Should not raise an exception for {} response.'.format(error))
                else:
                    if not error == requests.codes.not_found:
                        self.fail('Should raise an exception for {} response.'.format(error))

    def test_delete_email_notification_channel(self):
        """
        Check that the delete_email_notification_channel function behaves correctly if DELETE request unsuccessful.

        We expect the function *not* to raise an exception if the notification channel to delete
        can not be found (i.e., if the DELETE request comes back with a 404).

        In all other cases the function should raise an exception.
        """
        channel_id = 1

        client_errors = [status_code for status_code in requests.status_codes._codes if 400 <= status_code < 500]
        server_errors = [status_code for status_code in requests.status_codes._codes if 500 <= status_code < 600]

        for error in client_errors + server_errors:
            with responses.RequestsMock() as mock_responses:
                mock_responses.add(
                    responses.DELETE,
                    '{}/{}.json'.format(newrelic.ALERTS_CHANNELS_API_URL, channel_id),
                    status=error
                )
                try:
                    newrelic.delete_email_notification_channel(channel_id)
                except requests.exceptions.HTTPError:
                    if error == requests.codes.not_found:
                        self.fail('Should not raise an exception for {} response.'.format(error))
                else:
                    if not error == requests.codes.not_found:
                        self.fail('Should raise an exception for {} response.'.format(error))

    def test_delete_alert_condition(self):
        """
        Check that the delete_alert_condition function behaves correctly if DELETE request unsuccessful.

        We expect the function *not* to raise an exception if the alert_condition to delete
        can not be found (i.e., if the DELETE request comes back with a 404).

        In all other cases the function should raise an exception.
        """
        condition_id = 1

        client_errors = [status_code for status_code in requests.status_codes._codes if 400 <= status_code < 500]
        server_errors = [status_code for status_code in requests.status_codes._codes if 500 <= status_code < 600]

        for error in client_errors + server_errors:
            with responses.RequestsMock() as mock_responses:
                mock_responses.add(
                    responses.DELETE,
                    '{}/{}.json'.format(newrelic.ALERTS_CONDITIONS_API_URL, condition_id),
                    status=error
                )
                try:
                    newrelic.delete_alert_condition(condition_id)
                except requests.exceptions.HTTPError:
                    if error == requests.codes.not_found:
                        self.fail('Should not raise an exception for {} response.'.format(error))
                else:
                    if not error == requests.codes.not_found:
                        self.fail('Should raise an exception for {} response.'.format(error))
