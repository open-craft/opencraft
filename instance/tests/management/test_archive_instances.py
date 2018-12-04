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
Instance - Archive instances command unit tests
"""
# Imports #####################################################################

import os

from unittest.mock import patch, MagicMock

from django.core.management import call_command, CommandError
from django.utils.six import StringIO
from django.test import TestCase

from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.base import get_fixture_filepath


# Tests #######################################################################

class ArchiveInstancesTestCase(TestCase):
    """
    Test cases for the `archive_instances` management command.
    """
    def setUp(self):
        """
        Set up properties used to verify captured logs
        """
        super().setUp()
        self.cmd_module = 'instance.management.commands.archive_instances'
        self.log_level = 'INFO'

    def test_required_args(self):
        """
        Verify that the command correctly requires at least one domain parameter.
        """
        with self.assertRaisesRegex(CommandError, 'Error: either domain or --file are required'):
            call_command('archive_instances')

    @patch('instance.management.commands.archive_instances.input', MagicMock(return_value='no'))
    def test_no_archive(self):
        """
        Verify that the user can cancel the archiving by answering "no"
        """
        out = StringIO()
        call_command('archive_instances', 'foo.example.com', stdout=out)
        self.assertTrue(out.getvalue().strip().endswith('Cancelled'))

    @patch('instance.management.commands.archive_instances.input', MagicMock(return_value='yes'))
    def test_yes_archive(self):
        """
        Verify that the user can continue with the archiving by answering "yes"
        """
        out = StringIO()
        call_command('archive_instances', 'foo.example.com', stdout=out)
        self.assertRegex(out.getvalue(), 'Archived 0 instances.')

    def test_force_archive(self):
        """
        Verify that the user is not promped when --force is provided
        """
        out = StringIO()
        call_command('archive_instances', 'foo.example.com', '--force', stdout=out)
        self.assertRegex(out.getvalue(), 'Archived 0 instances.')

    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    @patch('instance.models.mixins.rabbitmq.RabbitMQInstanceMixin.deprovision_rabbitmq')
    def test_archiving_instances(self, mock_reconfigure, mock_disable_monitoring,
                                 mock_remove_dns_records, mock_deprovision_rabbitmq):
        """
        Test archiving single and multiple instances.
        """
        instances = self.create_test_instances()

        out = StringIO()
        call_command('archive_instances', 'A.example.com', '--force', stdout=out)
        self.assertRegex(out.getvalue(), 'Archived 1 instances.')
        instance = instances['A']['instance']
        instance.refresh_from_db()
        self.assertTrue(instance.ref.is_archived)
        self.assertEqual(mock_deprovision_rabbitmq.call_count, 1)

        # archive multiple instances
        # instance B is already archived, so should be ignored
        out = StringIO()
        call_command('archive_instances', 'B.example.com', 'C.example.com', 'D.example.com', '--force', stdout=out)
        self.assertRegex(out.getvalue(), 'Archived 2 instances.')
        for label in 'BCD':
            instance = instances[label]['instance']
            instance.refresh_from_db()
            self.assertTrue(instance.ref.is_archived)
        self.assertEqual(mock_deprovision_rabbitmq.call_count, 3)

        # archive using a file
        out = StringIO()
        fp = get_fixture_filepath(os.path.join('management', 'archive_instances.txt'))
        call_command('archive_instances', '--file=%s' % fp, '--force', stdout=out)
        self.assertRegex(out.getvalue(), 'Archived 3 instances.')
        for label in 'EFG':
            instance = instances[label]['instance']
            instance.refresh_from_db()
            self.assertTrue(instance.ref.is_archived)
        self.assertEqual(mock_deprovision_rabbitmq.call_count, 6)

        # archive using a file, domain positional arg is ignored
        out = StringIO()
        fp = get_fixture_filepath(os.path.join('management', 'archive_instances2.txt'))
        call_command('archive_instances', 'I.example.com', '--file=%s' % fp, '--force', stdout=out)
        self.assertRegex(out.getvalue(), 'Archived 1 instances.')
        instance = instances['H']['instance']
        instance.refresh_from_db()
        self.assertTrue(instance.ref.is_archived)
        self.assertEqual(mock_deprovision_rabbitmq.call_count, 7)

        instance = instances['I']['instance']
        instance.refresh_from_db()
        self.assertFalse(instance.ref.is_archived)

    @staticmethod
    def create_test_instances():
        """
        Create instances to test archiving.
        """
        # Create test instances with known attributes, and mock out the appserver_set
        instances = {}
        for label in 'ABCDEFGHI':

            # Create an instance, with an appserver
            instance = OpenEdXInstance.objects.create(
                sub_domain=label,
                openedx_release='z.1',
                successfully_provisioned=True
            )
            appserver = make_test_appserver(instance)

            # Transition the appserver through the various statuses to "running"
            appserver._status_to_waiting_for_server()
            appserver._status_to_configuring_server()
            appserver._status_to_running()

            instances[label] = dict(instance=instance, appserver=appserver)

        # Archive Instance B, so it won't match the filter
        instances['B']['instance'].ref.is_archived = True
        instances['B']['instance'].save()

        return instances
