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
Logger models & mixins - Tests
"""

# Imports #####################################################################

from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import override_settings
from freezegun import freeze_time

from instance.models.log_entry import LogEntry
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.server import OpenStackServerFactory


# Tests #######################################################################

class LoggingTestCase(TestCase):
    """
    Test cases for logging
    """
    def setUp(self):
        """
        Set up an instance and server to use for testing.
        """
        super().setUp()
        self.instance = OpenEdXInstanceFactory(sub_domain='my.instance', name="Test Instance 1")
        self.app_server = make_test_appserver(instance=self.instance)
        self.server = self.app_server.server

        # Override the VM names for consistency:
        patcher = patch('instance.models.server.OpenStackServer.name', new='test-vm-name')
        self.addCleanup(patcher.stop)
        patcher.start()

        # Expected log line prefixes based on the above:
        self.instance_prefix = 'instance.models.instance  | instance={} (Test Instance 1) | '.format(
            self.instance.ref.pk
        )
        self.appserver_prefix = (
            'instance.models.appserver | instance={} (Test Instance 1),app_server={} (AppServer 1) | '.format(
                self.instance.ref.pk, self.app_server.pk
            )
        )
        self.server_prefix = 'instance.models.server    | server=test-vm-name | '

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
        log_entry = LogEntry(text='OHAI')
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

        expected = [
            ("2015-08-05 18:07:00", 'INFO', self.instance_prefix + 'Line #1, on instance'),
            ("2015-08-05 18:07:03", 'INFO', self.instance_prefix + 'Line #4, on instance'),
            ("2015-08-05 18:07:04", 'WARNING', self.instance_prefix + 'Line #5, on instance (warn)'),
        ]
        self.check_log_entries(self.instance.log_entries, expected)

        expected = [
            ("2015-08-05 18:07:01", 'INFO', self.server_prefix + 'Line #2, on server'),
            ("2015-08-05 18:07:05", 'INFO', self.server_prefix + 'Line #6, on server'),
            ("2015-08-05 18:07:06", 'CRITICAL', self.server_prefix + 'Line #7, exception'),
        ]
        self.check_log_entries(self.app_server.log_entries, expected)

        # Check that the `LOG_LIMIT` setting is respected
        with override_settings(LOG_LIMIT=2):
            self.check_log_entries(self.app_server.log_entries, expected[-2:])

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
                'text': (
                    'instance.models.instance  | instance={} (Test Instance 1) | Text the client should see'.format(
                        self.instance.ref.pk
                    )
                ),
            },
            'type': 'object_log_line',
            'instance_id': self.instance.ref.pk,
            'instance_type': 'OpenEdXInstance',
        })

        with freeze_time("2015-09-21 21:07:01"):
            self.server.logger.info('Text the client should also see, with unicode «ταБЬℓσ»')

        mock_publish_data.assert_called_with('log', {
            'log_entry': {
                'created': '2015-09-21T21:07:01Z',
                'level': 'INFO',
                'text': ('instance.models.server    | server=test-vm-name | Text the client '
                         'should also see, with unicode «ταБЬℓσ»'),
            },
            'type': 'object_log_line',
            'server_id': self.server.pk,
        })

    def test_log_delete(self):
        """
        Check `log_entries` output for combination of instance & server logs
        """
        server1 = self.server
        server2 = OpenStackServerFactory(openstack_id='vm2_id')

        self.instance.logger.info('Line #1, on instance')
        server1.logger.info('Line #2, on server 1')
        server2.logger.info('Line #3, on server 2')

        self.assertEqual(LogEntry.objects.count(), 3)
        # Delete server 1:
        server1_id = server1.pk
        server1.delete()
        # Now its log entry should be deleted:
        entries = LogEntry.objects.order_by('pk').all().values_list('text', flat=True)
        for entry_text in entries:
            self.assertNotIn('Line #2', entry_text)
        self.assertIn('Line #1, on instance', entries[0])
        self.assertIn('Line #3, on server 2', entries[1])
        self.assertIn(
            'Deleted 1 log entries for deleted OpenStack VM instance with ID {}'.format(server1_id),
            entries[2]
        )

    def test_log_num_queries(self):
        """
        Check that logging to the LogEntry table doesn't do more queries than necessary.

        The expected queries upon inserting a log entry are:
        1. SELECT (1) AS "a" FROM "django_content_type" WHERE "django_content_type"."id" = {content_type_id} LIMIT 1
        2. SELECT (1) AS "a" FROM "instance_openstackserver" WHERE "instance_openstackserver"."id" = {object_id} LIMIT 1
        3. INSERT INTO "instance_logentry" (...)

        The first two are used to validate the foreign keys. 1. is added by django, and 2. is
        added by us since the object_id foreign key constraint is not enforced by the database.
        """
        with self.assertNumQueries(3):
            self.server.logger.info('some log message')

    def test_log_delete_num_queries(self):
        """
        Check that the LogEntry.on_post_delete handler doesn't do more queries than necessary.
        """
        server = OpenStackServerFactory()  # Can't use self.server since deletion of it cascades to self.app_server
        with self.assertNumQueries(3):
            # We expect one query to check for a related appserver, one to delete the server, one to delete the LogEntry
            server.delete()
        log_entry = LogEntry.objects.create(text='blah')
        with self.assertNumQueries(1):
            log_entry.delete()

    def test_str_repr(self):
        """
        Test the string representation of a LogEntry object
        """
        msg = 'We have entered a spectacular binary star system in the Kavis Alpha sector'
        with freeze_time("2015-10-20 20:10:15"):
            self.server.logger.info(msg)
        log_entry = LogEntry.objects.order_by('-pk')[0]
        self.assertEqual(
            str(log_entry),
            '2015-10-20 20:10:15 |     INFO | instance.models.server    | server=test-vm-name | ' + msg,
        )

    def test_invalid_content_type_object_id_combo(self):
        """
        Test that content_type and object_id cannot be set on their own
        """
        text = 'We are en route to Mintaka III.'

        def check_exception(exc):
            """ Check that the given exception contains the expected message """
            self.assertEqual(
                exc.messages,
                ['LogEntry content_type and object_id must both be set or both be None.'],
            )

        with self.assertRaises(ValidationError) as context:
            LogEntry.objects.create(text=text, content_type_id=None, object_id=self.server.pk)
        check_exception(context.exception)

        content_type = ContentType.objects.get_for_model(self.server)
        with self.assertRaises(ValidationError) as context:
            LogEntry.objects.create(text=text, content_type_id=content_type.pk, object_id=None)
        check_exception(context.exception)

    def test_invalid_object_id(self):
        """
        Test that object_id validity is enforced at the application level.
        """
        content_type = ContentType.objects.get_for_model(self.server)
        with self.assertRaises(ValidationError) as context:
            LogEntry.objects.create(
                text='We are departing the Rana system for Starbase 133.',
                content_type=content_type,
                object_id=987654321,  # An invalid ID
            )
        self.assertEqual(
            context.exception.messages,
            ['Object attached to LogEntry has bad content_type or primary key'],
        )

    def test_log_error_entries(self):
        """
        Check `log_error_entries` output for combination of AppServer & server logs
        """
        with freeze_time("2015-08-05 18:07:00"):
            self.app_server.logger.info('Line #1, on app_server')

        with freeze_time("2015-08-05 18:07:01"):
            self.app_server.logger.error('Line #2, on app_server')

        with freeze_time("2015-08-05 18:07:02"):
            self.app_server.logger.debug('Line #3, on app_server (debug, not published by default)')

        with freeze_time("2015-08-05 18:07:03"):
            self.server.logger.critical('Line #4, on server')

        with freeze_time("2015-08-05 18:07:04"):
            self.app_server.logger.warn('Line #5, on app_server (warn)')

        with freeze_time("2015-08-05 18:07:05"):
            self.server.logger.info('Line #6, on server')

        with freeze_time("2015-08-05 18:07:06"):
            self.app_server.logger.critical('Line #7, exception')

        self.instance.logger.critical("Instance-level errors should be excluded.")

        entries = self.app_server.log_error_entries
        self.assertEqual(len(entries), 3)

        self.assertEqual(entries[0].level, "ERROR")
        self.assertEqual(entries[0].created.strftime("%Y-%m-%d %H:%M:%S"), "2015-08-05 18:07:01")
        self.assertEqual(entries[0].text, self.appserver_prefix + "Line #2, on app_server")

        self.assertEqual(entries[1].level, "CRITICAL")
        self.assertEqual(entries[1].created.strftime("%Y-%m-%d %H:%M:%S"), "2015-08-05 18:07:03")
        self.assertEqual(entries[1].text, self.server_prefix + "Line #4, on server")

        self.assertEqual(entries[2].level, "CRITICAL")
        self.assertEqual(entries[2].created.strftime("%Y-%m-%d %H:%M:%S"), "2015-08-05 18:07:06")
        self.assertEqual(entries[2].text, self.appserver_prefix + "Line #7, exception")
