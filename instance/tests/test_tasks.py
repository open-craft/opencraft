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
Worker tasks - Tests
"""

# Imports #####################################################################

from mock import patch

from instance import github, tasks
from instance.models.instance import OpenEdXInstance
from instance.tests.base import TestCase
from instance.tests.models.factories.instance import OpenEdXInstanceFactory


# Tests #######################################################################

# Factory boy doesn't properly support pylint+django
#pylint: disable=no-member

class TasksTestCase(TestCase):
    """
    Test cases for worker tasks
    """
    @patch('instance.models.instance.OpenEdXInstance.provision', autospec=True)
    def test_provision_sandbox_instance(self, mock_instance_provision):
        """
        Create sandbox instance
        """
        instance = OpenEdXInstanceFactory()
        tasks.provision_instance(instance.pk)
        self.assertEqual(mock_instance_provision.call_count, 1)
        self.assertEqual(mock_instance_provision.mock_calls[0][1][0].pk, instance.pk)

    @patch('instance.models.instance.github.get_commit_id_from_ref')
    @patch('instance.tasks.provision_instance')
    @patch('instance.tasks.get_pr_list_from_username')
    @patch('instance.tasks.get_username_list_from_team')
    def test_watch_pr_new(self, mock_get_username_list, mock_get_pr_list_from_username,
                          mock_provision_instance, mock_get_commit_id_from_ref):
        """
        New PR created on the watched repo
        """
        mock_get_username_list.return_value = ['itsjeyd']
        pr = github.PR(
            number=234,
            fork_name='watched/fork',
            branch_name='watch-branch',
            title='Watched PR title which is very long',
            username='bradenmacdonald',
            body='Hello watcher!\n- - -\r\n**Settings**\r\n```\r\nWATCH: true\r\n```\r\nMore...',
        )
        self.assertEqual(pr.github_pr_url, 'https://github.com/watched/fork/pull/234')
        mock_get_pr_list_from_username.return_value = [pr]
        mock_get_commit_id_from_ref.return_value = '7' * 40

        tasks.watch_pr()
        self.assertEqual(mock_provision_instance.call_count, 1)
        instance = OpenEdXInstance.objects.get(pk=mock_provision_instance.mock_calls[0][1][0])
        self.assertEqual(instance.sub_domain, 'pr234.sandbox')
        self.assertEqual(instance.fork_name, 'watched/fork')
        self.assertEqual(instance.github_pr_number, 234)
        self.assertEqual(instance.github_pr_url, 'https://github.com/watched/fork/pull/234')
        self.assertEqual(instance.branch_name, 'watch-branch')
        self.assertEqual(instance.ansible_extra_settings, 'WATCH: true\r\n')
        self.assertEqual(
            instance.name,
            'PR#234: Watched PR title which ... (bradenmacdonald) - watched/watch-branch (7777777)')
