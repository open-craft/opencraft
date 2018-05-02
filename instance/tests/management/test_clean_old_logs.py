# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
Instance - Old logs cleaner task unit tests
"""
# Imports #####################################################################

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

from freezegun import freeze_time

from instance.models.log_entry import LogEntry
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory

# The clean_old_logs command replaces lines by a single line which starts with this message
DELETED_LOGS_MESSAGE = 'Logs were deleted'

# Tests #######################################################################


class CleanOldLogsTestCase(TestCase):
    """
    Test cases for the `clean_old_logs` management command.
    """
    def setUp(self):
        """
        Set up properties used to verify captured logs
        """
        super().setUp()
        self.cmd_module = 'instance.management.commands.clean_old_logs'
        self.log_level = 'INFO'

        self._create_servers_and_logs()

    def _create_servers_and_logs(self):
        """
        Creates instance 10 (with appservers 11, 12, 13) and instance 20 with one (21), and logs some lines.
        AppServers 11 and 12 will be considered old, and 13 and 21 will be recent.
        All instance and appservers will contain 1 log line, but appserver 12 will have 3.
        Note that we create and log in OpenEdxAppServer, not in OpenStackServer.
        """

        with freeze_time("2000-01-01 00:10:00"):
            self.instance10 = OpenEdXInstanceFactory(sub_domain='my.instance10', name="Test Instance 10")

        with freeze_time("2000-01-01 00:11:00"):
            self.app_server11 = make_test_appserver(instance=self.instance10)
        with freeze_time("2000-01-01 00:12:00"):
            self.app_server12 = make_test_appserver(instance=self.instance10)
        with freeze_time("2000-08-01 00:13:00"):
            self.app_server13 = make_test_appserver(instance=self.instance10)

        with freeze_time("2000-08-01 00:20:00"):
            self.instance20 = OpenEdXInstanceFactory(sub_domain='my.instance20', name="Test Instance 20")

        with freeze_time("2000-08-01 00:21:00"):
            self.app_server21 = make_test_appserver(instance=self.instance20)

        # Log something in all of them
        self.instance10.logger.info('Line #1, on instance 10')
        self.app_server11.logger.info('Line #2, on appserver 11')
        self.app_server11.logger.info('Line #3, on appserver 11')
        self.app_server11.logger.info('Line #4, on appserver 11')
        self.app_server12.logger.info('Line #5, on appserver 12')
        self.app_server13.logger.info('Line #6, on appserver 13')
        self.instance20.logger.info('Line #7, on instance 20')
        self.app_server21.logger.info('Line #8, on appserver 21')

        instance_type = ContentType.objects.get_for_model(self.instance10)
        appserver_type = ContentType.objects.get_for_model(self.app_server11)
        server_type = ContentType.objects.get_for_model(self.app_server11.server)

        # Verify setup
        self.assertEqual(LogEntry.objects.filter(content_type=instance_type).count(), 2)
        self.assertEqual(LogEntry.objects.filter(content_type=appserver_type).count(), 6)
        self.assertEqual(LogEntry.objects.filter(content_type=server_type).count(), 0)

    def test_log_cleaning(self):
        """
        Test log deletion of old appservers logs.
        It simulates to be at such a date that only appserver 11 and 12 are more than 6 months old.
        11 has many log lines, 12 has just one.
        It verifies that only appserver logs are removed, not instance logs.
        """
        with freeze_time("2000-08-30 00:00:00"):

            call_command('clean_old_logs', '--months-old=6', stdout=StringIO())

            # 11 and 12's logs were deleted
            self.assertEqual(len(list(self.app_server11.log_entries)), 1)
            self.assertIn(DELETED_LOGS_MESSAGE, list(self.app_server11.log_entries)[0].text)
            self.assertEqual(len(list(self.app_server12.log_entries)), 1)
            self.assertTrue(DELETED_LOGS_MESSAGE, list(self.app_server12.log_entries)[0].text)

            # 13 was recent, logs weren't deleted
            self.assertEqual(len(list(self.app_server13.log_entries)), 1)
            self.assertIn('Line #6, on appserver 13', list(self.app_server13.log_entries)[0].text)

            # 21 also not deleted
            self.assertEqual(len(list(self.app_server21.log_entries)), 1)
            self.assertIn('Line #8, on appserver 21', list(self.app_server21.log_entries)[0].text)

            # The instance logs weren't deleted
            self.assertEqual(len(list(self.instance10.log_entries)), 1)
            self.assertIn('Line #1, on instance 10', list(self.instance10.log_entries)[0].text)
            self.assertEqual(len(list(self.instance20.log_entries)), 1)
            self.assertIn('Line #7, on instance 20', list(self.instance20.log_entries)[0].text)

            # Verify new totals. 2 log lines were lost because #2, #3, #4 were replaced by a single line
            instance_type = ContentType.objects.get_for_model(self.instance10)
            appserver_type = ContentType.objects.get_for_model(self.app_server11)
            server_type = ContentType.objects.get_for_model(self.app_server11.server)

            self.assertEqual(LogEntry.objects.filter(content_type=instance_type).count(), 2)
            self.assertEqual(LogEntry.objects.filter(content_type=appserver_type).count(), 4)
            self.assertEqual(LogEntry.objects.filter(content_type=server_type).count(), 0)
