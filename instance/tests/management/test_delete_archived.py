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
delete_archived management command unit tests
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock

import ddt
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase

from instance.models.instance import InstanceReference
from instance.models.openedx_instance import OpenEdXInstance


@ddt.ddt
class DeleteArchivedTestCase(TestCase):
    """
    Test cases for the `delete_archived` management command.
    """

    def setUp(self):
        """
        Set up properties used to verify captured logs
        """
        super().setUp()
        self.cmd_module = 'instance.management.commands.archive_instances'
        self.log_level = 'INFO'

        # Instances name and days since modified
        instances = [
            ('newest', 1),
            ('new', 60),
            ('old', 200),
        ]

        with patch(
                'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
                return_value=(1, True)
        ):
            for name, days in instances:
                instance = OpenEdXInstance.objects.create(
                    sub_domain=name,
                    openedx_release='z.1',
                    successfully_provisioned=True
                )
                instance.ref.is_archived = True
                instance.ref.modified -= timedelta(days=days)
                instance.ref.save(update_modified=False)

    def test_zero_instances_deleted(self):
        """
        Verify that if no archived instances is old enough, the command exits
        without prompting.
        """
        out = StringIO()
        call_command('delete_archived', '24', stdout=out)
        self.assertTrue('No archived instances older than 24 months found.' in out.getvalue())

    @patch('instance.management.commands.delete_archived.input', MagicMock(return_value='no'))
    def test_cancel_deletion(self):
        """
        Verify that the user can cancel the deletion by answering "no"
        """
        out = StringIO()
        call_command('delete_archived', '0', stdout=out)
        self.assertTrue('Cancelled' in out.getvalue())

    @patch('instance.management.commands.delete_archived.input', MagicMock(return_value='yes'))
    @patch('instance.models.openedx_instance.OpenEdXInstance.delete')
    def test_confirm_deletion(self, mock_delete):
        """
        Verify deletion proceeds by answering "yes"
        """
        out = StringIO()
        call_command('delete_archived', '1', stdout=out)
        self.assertTrue('Found 2 archived instances older than 1 months' in out.getvalue())
        self.assertTrue('Deleting old.example.com' in out.getvalue())
        self.assertTrue('Deleting new.example.com' in out.getvalue())
        self.assertTrue('Deleted 2 archived instances older than 1 months' in out.getvalue())
        self.assertTrue('Deleting newer.example.com' not in out.getvalue())
        self.assertTrue('Failed to delete' not in out.getvalue())
        self.assertEqual(mock_delete.call_count, 2)

    @patch('instance.models.instance.InstanceReference.delete', MagicMock(side_effect=Exception('error')))
    def test_deletion_fails(self):
        """
        Verify '-y' skips confirmation and errors are logged
        """
        out = StringIO()
        err = StringIO()
        call_command('delete_archived', '-y', '3', stdout=out, stderr=err)
        self.assertTrue('Found 1 archived instances older than 3 months' in out.getvalue())

        self.assertTrue('Deleting old.example.com' in out.getvalue())
        self.assertTrue('Deleting new.example.com' not in out.getvalue())
        self.assertTrue('Deleting newer.example.com' not in out.getvalue())

        self.assertTrue('Failed to delete Instance' in out.getvalue())
        self.assertTrue('Failed to delete Instance' in err.getvalue())
        self.assertTrue('Traceback' in out.getvalue())
        self.assertTrue('Deleted 0 archived instances older than 3 months' in out.getvalue())

    @patch('instance.management.commands.delete_archived.input', MagicMock(return_value='yes'))
    @patch('instance.models.instance.InstanceReference.delete')
    @patch('instance.models.openedx_instance.OpenEdXInstance.delete')
    def test_ref_without_instance(self, mock_delete, mock_ref_delete):
        """
        Verify deletion proceeds when an InstanceReference does not point to
        an OpenEdxInstance.
        """
        # Create instanceless InstanceReference
        ref = InstanceReference.objects.create(
            name='Instanceless', instance_id=999, instance_type_id=13, is_archived=True)
        ref.modified -= timedelta(days=365)
        ref.save(update_modified=False)

        # Run command
        out = StringIO()
        call_command('delete_archived', '10', stdout=out)

        # Check only the InstanceReference queryset gets deleted
        self.assertTrue('Found 1 archived instances older than 10 months' in out.getvalue())
        self.assertTrue('Instanceless: No instance associated' in out.getvalue())
        self.assertTrue('Deleted 1 archived instances older than 10 months' in out.getvalue())
        self.assertEqual(mock_delete.call_count, 0)
        self.assertEqual(mock_ref_delete.call_count, 1)
