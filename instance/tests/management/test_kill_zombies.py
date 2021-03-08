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
Tests for the 'kill_zombies' management command.
"""
# Imports #####################################################################

from unittest.mock import patch, call
from django.core import mail
from django.core.management import CommandError
from django.test import TestCase, override_settings
from instance.tasks import KillZombiesRunner

# Tests #######################################################################

# pylint: disable=bad-continuation


@override_settings(
    KILL_ZOMBIES_ENABLED=True,
    ADMINS=(
        ("admin1", "admin1@localhost"),
        ("admin2", "admin2@localhost"),
    ),
    OPENSTACK_REGION="some-region"
)
class KillZombiesPeriodicallyTestCase(TestCase):
    """
    Test cases for the `kill_zombies_task` periodic task.
    """
    @override_settings(KILL_ZOMBIES_ENABLED=False)
    @patch("instance.tasks.call_command")
    def test_toggle_task_false(self, mock_command):
        """
        Tests that the task can't be run if disabled
        through env variables
        """
        with self.assertRaises(ImportError):
            from instance.tasks import kill_zombies_task
            kill_zombies_task()
        self.assertFalse(mock_command.called)

    @patch("instance.tasks.call_command")
    def test_set_env_variables(self, mock_command):
        """
        Tests that the task passes env variables to
        the kill_zombies command call
        """
        test_runner = KillZombiesRunner()
        test_runner.run()
        first_call = call.mock_command("kill_zombies", region="some-region", dry_run=True)
        self.assertEqual(mock_command.mock_calls[0], first_call)
        mock_command.assert_called_with("kill_zombies", region="some-region")

    @patch.object(KillZombiesRunner, "trigger_warning")
    def test_get_zombie_servers_count(self, mock_trigger):
        """
        Tests that KillZombiesRunner.get_zombie_servers_count
        works as expected
        """
        test_runner = KillZombiesRunner()
        no_instances = """
        2021-02-26 14:16:12 | Starting kill_zombies
        2021-02-26 14:16:12 | No servers found in region some-region.
        """
        some_instances = """
        2021-02-26 14:16:12 | Starting kill_zombies
        2021-02-26 14:16:12 | Found 32 unterminated servers in region some-region.
        2021-02-26 14:16:12 | Would have terminated 32 zombies if this weren't a dry run.
        """
        bad_output = "qwerty"
        self.assertEqual(test_runner.get_zombie_servers_count(no_instances), 0)
        self.assertEqual(test_runner.get_zombie_servers_count(some_instances), 32)
        self.assertEqual(test_runner.get_zombie_servers_count(bad_output), 0)
        self.assertEqual(test_runner.get_zombie_servers_count(""), 0)

    @override_settings(KILL_ZOMBIES_WARNING_THRESHOLD=3)
    @patch.object(KillZombiesRunner, "get_zombie_servers_count", return_value=4)
    @patch.object(KillZombiesRunner, "trigger_warning")
    @patch("instance.tasks.call_command")
    def test_trigger_warning_if_over_threshold(
        self,
        mock_get_zombie_servers_count,
        mock_trigger_warning,
        mock_command
    ):
        """
        Tests that trigger_warning is called when the number
        of zombies to delete is over the threshold
        """
        test_runner = KillZombiesRunner()
        test_runner.run()
        self.assertTrue(mock_get_zombie_servers_count.called)
        self.assertTrue(mock_trigger_warning.called)

    @patch.object(KillZombiesRunner, "get_zombie_servers_count", return_value=0)
    @patch("instance.tasks.call_command")
    def test_do_nothing_if_zero(
        self,
        mock_get_zombie_servers_count,
        mock_command
    ):
        """
        Tests that only a dry_run is executed when
        the number of zombies to terminate is zero.
        """
        test_runner = KillZombiesRunner()
        test_runner.run()
        mock_get_zombie_servers_count.assert_called_with(
            "kill_zombies",
            region="some-region",
            dry_run=True
        )

    @override_settings(
        DEFAULT_FROM_EMAIL="from@site.com",
        ADMINS=(("admin3", "admin3@localhost"), ("admin4", "admin4@localhost"))
    )
    @patch("instance.tasks.call_command")
    def test_send_warning_email(self, mock_command):
        """
        Tests that trigger_warning sends an email when called
        """
        test_runner = KillZombiesRunner()
        test_runner.trigger_warning(5)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "is over the KILL_ZOMBIES_WARNING_THRESHOLD",
            mail.outbox[0].body
        )
        self.assertEqual(mail.outbox[0].from_email, "from@site.com")
        self.assertEqual(mail.outbox[0].to, ["admin3@localhost", "admin4@localhost"])

    @override_settings(
        DEFAULT_FROM_EMAIL="from@site.com",
        ADMINS=(("admin3", "admin3@localhost"),)
    )
    @patch.object(KillZombiesRunner, "get_zombie_servers_count", return_value=4)
    @patch.object(KillZombiesRunner, "trigger_warning")
    @patch("instance.tasks.call_command")
    def test_send_email_on_failure(
        self,
        mock_get_zombie_servers_count,
        mock_trigger_warning,
        mock_command
    ):
        """
        When call_command fails, it raises a CommandError.
        Tests that an email is sent when CommandError is raised
        """
        mock_command.side_effect = CommandError()
        test_runner = KillZombiesRunner()
        test_runner.run()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "Scheduled execution of `kill_zombies` command failed",
            mail.outbox[0].body
        )
        self.assertEqual(mail.outbox[0].from_email, "from@site.com")
        self.assertEqual(mail.outbox[0].to, ["admin3@localhost"])
