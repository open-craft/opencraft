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
Instance - Archive instances command unit tests
"""
# Imports #####################################################################

import os

from unittest.mock import patch, MagicMock

import ddt
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.base import get_fixture_filepath


# Tests #######################################################################

@ddt.ddt
@patch(
    'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
@patch('instance.models.openedx_instance.OpenEdXInstance.purge_consul_metadata')
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

    @staticmethod
    def create_test_instances(labels):
        """
        Create instances to test archiving.
        """
        # Create test instances with known attributes, and mock out the appserver_set
        instances = {}
        for label in labels:
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

            domain = label + '.example.com'
            instances[domain] = dict(instance=instance, appserver=appserver)

        return instances

    def test_zero_instances_archived(self, *mock):
        """
        Verify that if no instances match the domains, the command exits
        without prompting.
        """
        out = StringIO()
        call_command('archive_instances', '--domains=X.example.com', stdout=out)
        self.assertEqual(out.getvalue().strip(), 'No active instances found (from 1 domains).')

    @patch('instance.management.commands.archive_instances.input', MagicMock(return_value='no'))
    def test_cancel_archive(self, *mock):
        """
        Verify that the user can cancel the archiving by answering "no"
        """
        self.create_test_instances('A')
        out = StringIO()
        call_command('archive_instances', '--domains=A.example.com', stdout=out)
        self.assertTrue(out.getvalue().strip().endswith('Cancelled'))

    @patch('instance.models.openedx_instance.OpenEdXInstance.clean_up_appserver_dns_records')
    @patch('instance.management.commands.archive_instances.input', MagicMock(return_value='yes'))
    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    @patch('instance.models.mixins.rabbitmq.RabbitMQInstanceMixin.deprovision_rabbitmq')
    def test_confirm_archive(self, *mock):
        """
        Verify that the user can continue with the archiving by answering "yes"
        """
        self.create_test_instances('A')
        out = StringIO()
        call_command('archive_instances', '--domains=A.example.com', stdout=out)
        self.assertRegex(out.getvalue(), r'.*Found 1 instances \(from 1 domains\) to be archived\.\.\..*')
        self.assertRegex(out.getvalue(), r'.*- A.example.com.*')
        self.assertRegex(out.getvalue(), r'.*Archiving A.example.com\.\.\..*')
        self.assertRegex(out.getvalue(), r'.*Archived 1 instances \(from 1 domains\).*')

    @patch('instance.models.openedx_instance.OpenEdXInstance.clean_up_appserver_dns_records')
    @patch('instance.management.commands.archive_instances.input', MagicMock(return_value='yes'))
    @ddt.data([['A.example.com'], 1],
              [['B.example.com', 'C.example.com', 'D.example.com'], 2])
    @ddt.unpack
    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    @patch('instance.models.mixins.rabbitmq.RabbitMQInstanceMixin.deprovision_rabbitmq')
    def test_archiving_instances_by_domain(self, domains, expected_archived_count,
                                           mock_deprovision_rabbitmq, *mock):
        """
        Test archiving single and multiple instances by passing invidividual domains.
        """
        instances = self.create_test_instances('ABCDEFGH')
        # Mark instance B as archived, so it won't match the filter
        instances['B.example.com']['instance'].ref.is_archived = True
        instances['B.example.com']['instance'].save()

        patch('instance.management.commands.archive_instances.input', MagicMock(return_value='yes'))
        out = StringIO()
        call_command('archive_instances', '--domains=%s' % ','.join(domains), stdout=out)
        self.assertRegex(
            out.getvalue(),
            r'.*Archived {archived_count} instances \(from {domains_count} domains\).*'.format(
                archived_count=expected_archived_count, domains_count=len(domains)
            )
        )
        for domain in domains:
            instance = instances[domain]['instance']
            instance.refresh_from_db()
            self.assertTrue(instance.ref.is_archived)
        self.assertEqual(mock_deprovision_rabbitmq.call_count, expected_archived_count)

    @patch('instance.models.openedx_instance.OpenEdXInstance.clean_up_appserver_dns_records')
    @patch('instance.management.commands.archive_instances.input', MagicMock(return_value='yes'))
    @ddt.data(['archive_instances.txt', 3],
              ['archive_instances2.txt', 1])
    @ddt.unpack
    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    @patch('instance.models.mixins.rabbitmq.RabbitMQInstanceMixin.deprovision_rabbitmq')
    def test_archiving_instances_by_file(self, filename, expected_archived_count,
                                         mock_deprovision_rabbitmq, *mock):
        """
        Test archiving instances from domains listed in a file.
        """
        instances = self.create_test_instances('ABCDEFGH')

        out = StringIO()
        fp = get_fixture_filepath(os.path.join('management', filename))
        with open(fp, 'r') as f:
            domains = [line.strip() for line in f.readlines()]
        call_command('archive_instances', '--file=%s' % fp, stdout=out)
        self.assertRegex(
            out.getvalue(),
            r'.*Archived {archived_count} instances \(from {domains_count} domains\).'.format(
                archived_count=expected_archived_count, domains_count=len(domains)
            )
        )
        for domain in domains:
            instance = instances[domain]['instance']
            instance.refresh_from_db()
            self.assertTrue(instance.ref.is_archived)
        self.assertEqual(mock_deprovision_rabbitmq.call_count, expected_archived_count)

    @patch('instance.models.openedx_instance.OpenEdXInstance.clean_up_appserver_dns_records')
    @patch('instance.management.commands.archive_instances.input', MagicMock(return_value='yes'))
    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    @patch('instance.models.mixins.rabbitmq.RabbitMQInstanceMixin.deprovision_rabbitmq')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    def test_archive_exception_handling(self, mock_disable_monitoring, *mock):
        """
        Verify that if an instance fails to be archived, the other instances are still being archived.
        """
        instances = self.create_test_instances('ABCD')
        domains = instances.keys()

        # mock instance.disable_monitoring() method to raise exception for the first instance
        mock_disable_monitoring.side_effect = [Exception('disable_monitoring'), None, None, None]

        out = StringIO()
        call_command(
            'archive_instances',
            '--domains=%s' % ','.join(domains),
            stdout=out
        )
        self.assertRegex(out.getvalue(), r'.*Archived 3 instances \(from 4 domains\).')
        self.assertRegex(out.getvalue(), r'.*Failed to archive A.example.com.')
        self.assertEqual(
            OpenEdXInstance.objects.filter(internal_lms_domain__in=domains, ref_set__is_archived=True).count(),
            3
        )
