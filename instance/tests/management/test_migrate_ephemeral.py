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
Instance - migrate_ephemeral unit tests
"""
from unittest.mock import patch

from django.core.exceptions import FieldDoesNotExist
from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO
from testfixtures import LogCapture

from instance.models.openedx_instance import OpenEdXInstance


class MigrateEphemeralTestCase(TestCase):
    """
    Test cases for the `migrate_ephemeral` management command.
    """

    def test_no_instances(self):
        """
        Verify that the command correctly notifies the user that there are no instances for migration.
        """
        try:
            with LogCapture() as captured_logs:
                call_command(
                    'migrate_ephemeral',
                    stdout=StringIO(),
                )
                # Verify the logs
                self.assertIn(
                    'Found "0" instances using ephemeral databases',
                    [l[2] for l in captured_logs.actual()])
        except FieldDoesNotExist:
            # Field already removed from database
            pass

    @patch('instance.tasks.spawn_appserver')
    def test_migrate(self, mock_spawn_appserver):
        """
        Verify that the command correctly migrate an instance to use external databases.
        """
        try:
            OpenEdXInstance.objects.create(
                sub_domain='test_migrate', use_ephemeral_databases=True, name='test_migrate instance')
            with LogCapture() as captured_logs:
                call_command(
                    'migrate_ephemeral',
                    stdout=StringIO(),
                )
                # Verify the logs
                actual = set(l[2] for l in captured_logs.actual())
                expected = {
                    'Found "1" instances using ephemeral databases',
                    'Migrated and started provisioning a new app server for test_migrate instance',
                }
                self.assertTrue(expected <= actual)

            self.assertTrue(mock_spawn_appserver.called)
        except TypeError:
            # Field already removed from database
            pass
