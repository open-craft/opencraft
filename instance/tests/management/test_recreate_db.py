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
Tests for the 'recreate_db' management command.
"""
from io import StringIO
from textwrap import dedent
from unittest.mock import patch

from django.core.management import call_command, CommandError
from django.test import TestCase

from instance.models.openedx_instance import OpenEdXInstance


@patch(
    'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class RecreateDBTestCase(TestCase):
    """
    Tests the recreate_db command.
    """

    def setUp(self):
        """
        Set up our test buffers.
        """
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.input_patch = patch('instance.management.commands.recreate_db.input')
        self.mock_input = self.input_patch.start()
        self.mock_input.return_value = "Placeholder value so the process doesn't block."

    def tearDown(self):
        """
        Remove the input patch.
        """
        self.input_patch.stop()

    def execute(self, *args, **kwargs):
        """
        Wrapper for the call_command function that hands all our test buffers to it.
        """
        call_command(
            "recreate_db",
            *args,
            stdout=self.stdout,
            stderr=self.stderr,
            **kwargs,
        )

    def test_no_domain_match(self, _mock_consul):
        """
        Tests that the command fails if the user specifies an instance which doesn't exist.
        """
        with self.assertRaises(CommandError) as context:
            self.execute(domain='beep.boop', yes=True, admin='Jimbob', reason='Stuff broke.')
        self.assertEqual(
            str(context.exception),
            'An instance with the domain name "beep.boop" could not be found.'
        )

    def test_no_domain(self, _mock_consul):
        """
        Tests that the command fails if the user does not specify a domain.
        """
        with self.assertRaises(CommandError) as context:
            self.execute(yes=True, admin='Jimbob', reason='Stuff broke.')
        self.assertEqual(
            str(context.exception),
            'Error: the following arguments are required: --domain',
        )

    def test_no_admin_provided(self, _mock_consul):
        """
        Tests that the command fails if an admin's name isn't provided.
        """
        with self.assertRaises(CommandError) as context:
            self.execute(domain='beep.boop', yes=True, reason='Stuff broke.')
        self.assertEqual(
            str(context.exception),
            'Error: the following arguments are required: --admin',
        )

    def test_no_reason_provided(self, _mock_consul):
        """
        Tests that the command fails if a reason isn't provided.
        """
        with self.assertRaises(CommandError) as context:
            self.execute(domain='beep.boop', yes=True, admin='JimBob.')
        self.assertEqual(
            str(context.exception),
            'Error: the following arguments are required: --reason',
        )

    @patch('instance.models.openedx_instance.OpenEdXInstance.create_db')
    @patch('instance.models.openedx_instance.OpenEdXInstance.drop_db')
    def test_confirmation_prompt_yes(self, mock_drop, mock_create, _mock_consul):
        """
        Test that the conformation prompt handles an affirmative answer.
        """
        OpenEdXInstance.objects.create(
            internal_lms_domain='beep.boop',
            openedx_release='z.1',
            successfully_provisioned=False,
        )
        self.mock_input.return_value = 'yes'
        self.execute(domain='beep.boop', admin='JimBob.', reason='Stuff and things.')
        self.mock_input.assert_called_with('Are you sure you want to continue? [yes/No]')
        mock_drop.assert_called_with('edxapp')
        mock_create.assert_called_with('edxapp')

    @patch('instance.models.openedx_instance.OpenEdXInstance.create_db')
    @patch('instance.models.openedx_instance.OpenEdXInstance.drop_db')
    def test_confirmation_prompt_else(self, mock_drop, mock_create, _mock_consul):
        """
        Test that the command is aborted on a non-affirmative answer to the confirmation prompt.
        """
        OpenEdXInstance.objects.create(
            internal_lms_domain='beep.boop',
            openedx_release='z.1',
            successfully_provisioned=False,
        )
        self.mock_input.return_value = 'arf'
        with self.assertRaises(CommandError) as context:
            self.execute(domain='beep.boop', admin='JimBob.', reason='Stuff and things.')
        self.mock_input.assert_called_with('Are you sure you want to continue? [yes/No]')
        mock_drop.assert_not_called()
        mock_create.assert_not_called()
        self.assertEqual(
            str(context.exception),
            'Aborted.',
        )

    @patch('instance.models.openedx_instance.OpenEdXInstance.create_db')
    @patch('instance.models.openedx_instance.OpenEdXInstance.drop_db')
    def test_confirmation_prompt_skipped(self, mock_drop, mock_create, _mock_consul):
        """
        Test that the 'yes' flag successfully skips the prompt.
        """
        OpenEdXInstance.objects.create(
            internal_lms_domain='beep.boop',
            openedx_release='z.1',
            successfully_provisioned=False,
        )
        self.mock_input.return_value = "Don't block tests if we fail."
        self.execute(domain='beep.boop', admin='JimBob.', reason='Stuff and things.', yes=True)
        self.mock_input.assert_not_called()
        mock_drop.assert_called_with('edxapp')
        mock_create.assert_called_with('edxapp')

    @patch('instance.models.openedx_instance.OpenEdXInstance.create_db')
    @patch('instance.models.openedx_instance.OpenEdXInstance.drop_db')
    def test_fail_on_successfully_provisioned(self, mock_drop, mock_create, _mock_consul):
        """
        Verifies the command will bail out if the instance has already provisioned successfully.
        """
        OpenEdXInstance.objects.create(
            internal_lms_domain='beep.boop',
            openedx_release='z.1',
            successfully_provisioned=True,
        )
        with self.assertRaises(CommandError) as context:
            self.execute(domain='beep.boop', admin='JimBob.', reason='Stuff and things.', yes=True)
        mock_drop.assert_not_called()
        mock_create.assert_not_called()
        self.assertEqual(
            str(context.exception),
            'Cowardly refusing to drop the database of "beep.boop", which has already successfully '
            'provisioned at least once.',
        )

    @patch('instance.models.openedx_instance.OpenEdXInstance.create_db')
    @patch('instance.models.openedx_instance.OpenEdXInstance.drop_db')
    def test_log_entries(self, _mock_drop, _mock_create, _mock_consul):
        """
        Test that the expected log entries are created and bound to the instance.
        """
        instance = OpenEdXInstance.objects.create(
            internal_lms_domain='beep.boop',
            openedx_release='z.1',
            successfully_provisioned=False,
        )
        self.execute(domain='beep.boop', admin='JimBob', reason='Stuff and things.', yes=True)
        logs = '\n'.join((entry.text for entry in instance.log_entries))
        self.assertIn(
            dedent(
                """
                !!!
                ! Blowing away and recreating the edxapp database!
                ! Authorized by: JimBob
                ! Reason: Stuff and things.
                !!!
                """,
            ),
            logs,
        )
        self.assertIn('Dropping edxapp database...', logs)
        self.assertIn('DB Dropped. Recreating database...', logs)
        self.assertIn('DB Recreated successfully.', logs)
