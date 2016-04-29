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

import textwrap

from mock import patch

from instance import tasks
from instance.models.instance import SingleVMOpenEdXInstance
from instance.tests.base import TestCase
from instance.tests.factories.pr import PRFactory
from instance.tests.models.factories.instance import SingleVMOpenEdXInstanceFactory


# Tests #######################################################################

# Factory boy doesn't properly support pylint+django
#pylint: disable=no-member

class TasksTestCase(TestCase):
    """
    Test cases for worker tasks
    """
    @patch('instance.models.instance.SingleVMOpenEdXInstance.provision', autospec=True)
    def test_provision_sandbox_instance(self, mock_instance_provision):
        """
        Create sandbox instance
        """
        instance = SingleVMOpenEdXInstanceFactory()
        tasks.provision_instance(instance.pk)
        self.assertEqual(mock_instance_provision.call_count, 1)
        self.assertEqual(mock_instance_provision.mock_calls[0][1][0].pk, instance.pk)
        self.mock_db_connection_close.assert_called_once_with()

    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    @patch('instance.tasks.provision_instance')
    @patch('instance.tasks.get_pr_list_from_username')
    @patch('instance.tasks.get_username_list_from_team')
    def test_watch_pr_new(self, mock_get_username_list, mock_get_pr_list_from_username,
                          mock_provision_instance, mock_get_commit_id_from_ref):
        """
        New PR created on the watched repo
        """
        ansible_extra_settings = textwrap.dedent("""\
            WATCH: true
            edx_ansible_source_repo: https://github.com/open-craft/configuration
            configuration_version: named-release/elder
        """)
        mock_get_username_list.return_value = ['itsjeyd']
        pr = PRFactory(
            number=234,
            source_fork_name='fork/repo',
            target_fork_name='source/repo',
            branch_name='watch-branch',
            title='Watched PR title which is very long',
            username='bradenmacdonald',
            body='Hello watcher!\n- - -\r\n**Settings**\r\n```\r\n{}```\r\nMore...'.format(
                ansible_extra_settings
            ),
        )
        self.assertEqual(pr.github_pr_url, 'https://github.com/source/repo/pull/234')
        mock_get_pr_list_from_username.return_value = [pr]
        mock_get_commit_id_from_ref.return_value = '7' * 40

        tasks.watch_pr()
        self.assertEqual(mock_provision_instance.call_count, 1)
        instance = SingleVMOpenEdXInstance.objects.get(pk=mock_provision_instance.mock_calls[0][1][0])
        self.assertEqual(instance.sub_domain, 'pr234.sandbox')
        self.assertEqual(instance.fork_name, 'fork/repo')
        self.assertEqual(instance.github_pr_number, 234)
        self.assertEqual(instance.github_pr_url, 'https://github.com/source/repo/pull/234')
        self.assertEqual(instance.github_base_url, 'https://github.com/fork/repo')
        self.assertEqual(instance.branch_name, 'watch-branch')
        self.assertEqual(instance.ansible_extra_settings, ansible_extra_settings)
        self.assertEqual(instance.ansible_source_repo_url, 'https://github.com/open-craft/configuration')
        self.assertEqual(instance.configuration_version, 'named-release/elder')
        self.assertEqual(
            instance.name,
            'PR#234: Watched PR title which ... (bradenmacdonald) - fork/watch-branch (7777777)')
        self.mock_db_connection_close.assert_called_once_with()
