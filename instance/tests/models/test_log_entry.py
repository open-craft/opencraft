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
Logger models & mixins - Tests
"""

# Imports #####################################################################

from django.test import override_settings
from freezegun import freeze_time
from mock import patch

from instance.models.log_entry import GeneralLogEntry
from instance.tests.base import TestCase
from instance.tests.models.factories.instance import SingleVMOpenEdXInstanceFactory
from instance.tests.models.factories.server import OpenStackServerFactory


# Tests #######################################################################

# Factory boy doesn't properly support pylint+django
#pylint: disable=no-member

class LoggingTestCase(TestCase):
    """
    Test cases for logging
    """
    def setUp(self):
        """
        Set up an instance and server to use for testing.
        """
        super().setUp()
        self.instance = SingleVMOpenEdXInstanceFactory(sub_domain='my.instance')
        self.server = OpenStackServerFactory(instance=self.instance, openstack_id='vm1_id')

    def check_log_entries(self, entries, expected):
        """
        Check that the given entries match the expected log output.
        """
        for entry, (date, level, text) in zip(entries, expected):
            self.assertEqual(entry.created.strftime("%Y-%m-%d %H:%M:%S"), date)
            self.assertEqual(entry.level, level)
            self.assertEqual(entry.text, text)

    def test_default_log_level(self):
        """
        Check that the default log level is INFO
        """
        log_entry = GeneralLogEntry(text='OHAI')
        self.assertEqual(log_entry.level, 'INFO')

    def test_log_entries(self):
        """
        Check `log_entries` output for combination of instance & server logs
        """
        lines = [
            ("2015-08-05 18:07:00", self.instance.logger.info, 'Line #1, on instance'),
            ("2015-08-05 18:07:01", self.server.logger.info, 'Line #2, on server'),
            ("2015-08-05 18:07:02", self.instance.logger.debug,
             'Line #3, on instance (debug, not published by default)'),
            ("2015-08-05 18:07:03", self.instance.logger.info, 'Line #4, on instance'),
            ("2015-08-05 18:07:04", self.instance.logger.warn, 'Line #5, on instance (warn)'),
            ("2015-08-05 18:07:05", self.server.logger.info, 'Line #6, on server'),
            ("2015-08-05 18:07:06", self.server.logger.critical, 'Line #7, exception'),
        ]

        for date, log, text in lines:
            with freeze_time(date):
                log(text)

        instance_prefix = 'instance.models.instance  | instance=my.instance | '
        server_prefix = 'instance.models.server    | instance=my.instance,server=vm1_id | '
        expected = [
            ("2015-08-05 18:07:00", 'INFO', instance_prefix + 'Line #1, on instance'),
            ("2015-08-05 18:07:01", 'INFO', server_prefix + 'Line #2, on server'),
            ("2015-08-05 18:07:03", 'INFO', instance_prefix + 'Line #4, on instance'),
            ("2015-08-05 18:07:04", 'WARNING', instance_prefix + 'Line #5, on instance (warn)'),
            ("2015-08-05 18:07:05", 'INFO', server_prefix + 'Line #6, on server'),
            ("2015-08-05 18:07:06", 'CRITICAL', server_prefix + 'Line #7, exception'),
        ]
        self.check_log_entries(self.instance.log_entries, expected)

        # Check that the `LOG_LIMIT` setting is respected
        with override_settings(LOG_LIMIT=3):
            self.check_log_entries(self.instance.log_entries, expected[-3:])

    @patch('instance.logging.publish_data')
    def test_log_publish(self, mock_publish_data):
        """
        Logger sends an event to the client on each new log entry added
        """
        with freeze_time("2015-09-21 21:07:00"):
            self.instance.logger.info('Text the client should see')

        mock_publish_data.assert_called_with('log', {
            'log_entry': {
                'created': '2015-09-21T21:07:00Z',
                'level': 'INFO',
                'text': 'instance.models.instance  | instance=my.instance | Text the client should see',
            },
            'type': 'instance_log',
            'instance_id': self.instance.pk,
        })

        with freeze_time("2015-09-21 21:07:01"):
            self.server.logger.info('Text the client should also see, with unicode «ταБЬℓσ»')

        mock_publish_data.assert_called_with('log', {
            'log_entry': {
                'created': '2015-09-21T21:07:01Z',
                'level': 'INFO',
                'text': ('instance.models.server    | instance=my.instance,server=vm1_id | Text the client '
                         'should also see, with unicode «ταБЬℓσ»'),
            },
            'type': 'instance_log',
            'instance_id': self.instance.pk,
            'server_id': self.server.pk,
        })

    def test_log_error_entries(self):
        """
        Check `log_error_entries` output for combination of instance & server logs
        """
        with freeze_time("2015-08-05 18:07:00"):
            self.instance.logger.info('Line #1, on instance')

        with freeze_time("2015-08-05 18:07:01"):
            self.instance.logger.error('Line #2, on server')

        with freeze_time("2015-08-05 18:07:02"):
            self.instance.logger.debug('Line #3, on instance (debug, not published by default)')

        with freeze_time("2015-08-05 18:07:03"):
            self.server.logger.critical('Line #4, on instance')

        with freeze_time("2015-08-05 18:07:04"):
            self.instance.logger.warn('Line #5, on instance (warn)')

        with freeze_time("2015-08-05 18:07:05"):
            self.server.logger.info('Line #6, on server')

        with freeze_time("2015-08-05 18:07:06"):
            self.instance.logger.critical('Line #7, exception')

        entries = self.instance.log_error_entries
        self.assertEqual(entries[0].level, "ERROR")
        self.assertEqual(entries[0].created.strftime("%Y-%m-%d %H:%M:%S"), "2015-08-05 18:07:01")
        self.assertEqual(entries[0].text,
                         "instance.models.instance  | instance=my.instance | Line #2, on server")

        self.assertEqual(entries[1].level, "CRITICAL")
        self.assertEqual(entries[1].created.strftime("%Y-%m-%d %H:%M:%S"), "2015-08-05 18:07:03")
        self.assertEqual(entries[1].text,
                         "instance.models.server    | instance=my.instance,server=vm1_id | Line #4, on instance")

        self.assertEqual(entries[2].level, "CRITICAL")
        self.assertEqual(entries[2].created.strftime("%Y-%m-%d %H:%M:%S"), "2015-08-05 18:07:06")
        self.assertEqual(entries[2].text,
                         "instance.models.instance  | instance=my.instance | Line #7, exception")
