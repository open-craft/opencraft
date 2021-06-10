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
Instance - Logs Activity CSV unit tests
"""
# Imports #####################################################################

from argparse import ArgumentTypeError
from datetime import datetime, date, timedelta
from unittest.mock import patch, Mock, ANY

from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils.six import StringIO
from django.test import TestCase
import freezegun

from instance.management.commands.instance_statistics_csv import valid_date


# Tests #######################################################################

class ValidDateTestCase(TestCase):
    """
    Test cases for the `valid_date` helper function.
    """
    @freezegun.freeze_time('2020-01-01')
    def test_invalid_input(self):
        """
        Verify that invalid date strings error and provide reasonable message
        """
        with self.assertRaises(ArgumentTypeError) as context_manager:
            valid_date('invalid')
            self.assertIn('Not a valid date', str(context_manager.exception))

    @freezegun.freeze_time('2020-01-01')
    def test_date_in_future(self):
        """
        Verify that dates in the future error and provide reasonable message
        """
        with self.assertRaises(ArgumentTypeError) as context_manager:
            valid_date('2020-05-01')
            self.assertIn('Date must be earlier than or equal to today', str(context_manager.exception))

    @freezegun.freeze_time('2020-01-01')
    def test_today(self):
        """
        Verify that today works
        """
        self.assertEqual(valid_date('2020-01-01'), '2020-01-01')

    @freezegun.freeze_time('2020-01-01')
    def test_date_in_past(self):
        """
        Verify that a date in the past works
        """
        self.assertEqual(valid_date('2019-01-01'), '2019-01-01')


class InstanceStatisticsCSVTestCase(TestCase):
    """
    Test cases for the `instance_statistics_csv` management command.
    """
    def test_no_qualified_domain(self):
        """
        Verify that the command correctly notifies the user that the domain is required
        """
        with self.assertRaises(CommandError) as context_manager:
            call_command(
                'instance_statistics_csv'
            )
            self.assertIn('Error: the following arguments are required', str(context_manager.exception))

    @patch('instance.management.commands.instance_statistics_csv.open', Mock(side_effect=PermissionError))
    def test_unable_to_write_to_output(self):
        """
        Verify that the command correctly notifies the user when it is unable to write to the request output file
        """
        stderr = StringIO()
        with self.assertRaises(SystemExit):
            call_command(
                'instance_statistics_csv',
                domains='test',
                out='does_not_exist.txt',
                stderr=stderr
            )
        self.assertIn('Permission denied while attempting to write file', stderr.getvalue())

    def test_no_matching_instances(self):
        """
        Verify that the command correctly notifies the user that
        there are no matching instances.
        """
        stderr = StringIO()
        with self.assertRaises(SystemExit):
            call_command(
                'instance_statistics_csv',
                domains='test.opencraft.hosting',
                stderr=stderr
            )
        self.assertIn('No OpenEdXInstances exist with an external or internal domain', stderr.getvalue())

    @freezegun.freeze_time('2020-01-01')
    @patch('instance.management.commands.instance_statistics_csv.Command.collect_instance_statistics')
    @patch('instance.management.commands.instance_statistics_csv.open')
    @patch('instance.management.commands.instance_statistics_csv.Command.DEFAULT_NUM_DAYS', 10)
    def test_default_dates(self, mock_open, mock_collect_statistics):
        """
        Verify that the command uses correct default dates
        """
        outfile = 'somefile.txt'
        domain = 'test.opencraft.hosting'

        mock_file = Mock()
        mock_open.return_value = mock_file

        call_command(
            'instance_statistics_csv',
            domains=domain,
            out=outfile
        )

        expected_end_date = datetime.utcnow().date()
        expected_start_date = expected_end_date - timedelta(days=10)

        mock_collect_statistics.assert_called_with(
            mock_file,
            [domain],
            expected_start_date,
            expected_end_date
        )

    @freezegun.freeze_time('2020-01-01')
    @patch('instance.management.commands.instance_statistics_csv.open')
    def test_start_date_after_end_date_errors(self, mock_open):
        """
        Verify that the command errors when end-date is before start-date
        """
        outfile = 'somefile.txt'
        domain = 'test.opencraft.hosting'

        custom_end_date = '2019-01-01'
        custom_start_date = '2019-05-01'

        mock_file = Mock()
        mock_open.return_value = mock_file

        stderr = StringIO()
        with self.assertRaises(SystemExit):
            call_command(
                'instance_statistics_csv',
                domains=domain,
                end_date=custom_end_date,
                start_date=custom_start_date,
                out=outfile,
                stderr=stderr
            )

        self.assertIn('must be later than or equal to --start-date', stderr.getvalue())

    @freezegun.freeze_time('2020-01-01')
    @patch('instance.management.commands.instance_statistics_csv.Command.collect_instance_statistics')
    @patch('instance.management.commands.instance_statistics_csv.open')
    def test_custom_dates(self, mock_open, mock_collect_statistics):
        """
        Verify that the command uses custom dates
        """
        outfile = 'somefile.txt'
        domain = 'test.opencraft.hosting'

        custom_end_date = '2019-05-01'
        custom_start_date = '2019-01-01'

        mock_file = Mock()
        mock_open.return_value = mock_file

        call_command(
            'instance_statistics_csv',
            domains=domain,
            end_date=custom_end_date,
            start_date=custom_start_date,
            out=outfile
        )

        expected_end_date = date(2019, 5, 1)
        expected_start_date = date(2019, 1, 1)

        mock_collect_statistics.assert_called_with(
            mock_file,
            [domain],
            expected_start_date,
            expected_end_date
        )

    @freezegun.freeze_time('2020-01-01')
    @patch('instance.management.commands.instance_statistics_csv.Command.collect_instance_statistics')
    @patch('instance.management.commands.instance_statistics_csv.open')
    def test_multiple_domains(self, mock_open, mock_collect_statistics):
        """
        Verify that the command uses custom dates
        """
        outfile = 'somefile.txt'
        domain1 = 'test.opencraft.hosting'
        domain2 = 'another.opencraft.hosting'

        mock_file = Mock()
        mock_open.return_value = mock_file

        call_command(
            'instance_statistics_csv',
            domains=','.join([domain1, domain2]),
            out=outfile
        )

        expected_end_date = datetime.utcnow().date()
        expected_start_date = expected_end_date - timedelta(days=30)

        mock_collect_statistics.assert_called_with(
            mock_file,
            [domain1, domain2],
            expected_start_date,
            expected_end_date
        )

    @freezegun.freeze_time('2020-01-01')
    @patch('instance.management.commands.instance_statistics_csv.Command.get_instances_from_domain_names')
    @patch('instance.management.commands.instance_statistics_csv.Command.get_instance_usage_data')
    @patch('instance.management.commands.instance_statistics_csv.open')
    def test_custom_dates_for_get_instance_usage_data(self, mock_open, mock_get_instance_usage_data, mock_unused):
        """
        Verify that the custom dates are passed to get_instance_usage_data
        """
        outfile = 'somefile.txt'
        domain = 'test.opencraft.hosting'

        custom_end_date = '2019-05-01'
        custom_start_date = '2019-01-01'

        mock_file = Mock()
        mock_open.return_value = mock_file

        call_command(
            'instance_statistics_csv',
            domains=domain,
            end_date=custom_end_date,
            start_date=custom_start_date,
            out=outfile
        )

        expected_end_date = date(2019, 5, 1)
        expected_start_date = date(2019, 1, 1)

        mock_get_instance_usage_data.assert_called_with(
            ANY,
            ANY,
            expected_start_date,
            expected_end_date
        )
