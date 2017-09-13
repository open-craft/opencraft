# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
from unittest.mock import patch

from django.test import TestCase, override_settings

from instance.models.openedx_instance import OpenEdXInstance
from pr_watch import tasks
from pr_watch.github import RateLimitExceeded
from pr_watch.models import WatchedPullRequest
from pr_watch.tests.factories import PRFactory


# Tests #######################################################################


class TasksTestCase(TestCase):
    """
    Test cases for PR Watcher worker tasks
    """
    @patch('pr_watch.github.get_commit_id_from_ref')
    @patch('pr_watch.tasks.spawn_appserver')
    @patch('pr_watch.tasks.get_pr_list_from_usernames')
    @patch('pr_watch.tasks.get_username_list_from_team')
    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='awesome.hosting.org')
    def test_watch_pr_new(self, mock_get_username_list, mock_get_pr_list_from_usernames,
                          mock_spawn_appserver, mock_get_commit_id_from_ref):
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
        pr_url = 'https://github.com/source/repo/pull/234'
        self.assertEqual(pr.github_pr_url, pr_url)
        mock_get_pr_list_from_usernames.return_value = [pr]
        mock_get_commit_id_from_ref.return_value = '7' * 40

        tasks.watch_pr()
        self.assertEqual(mock_spawn_appserver.call_count, 1)
        new_instance_ref_id = mock_spawn_appserver.mock_calls[0][1][0]
        instance = OpenEdXInstance.objects.get(ref_set__pk=new_instance_ref_id)
        self.assertEqual(instance.internal_lms_domain, 'pr234.sandbox.awesome.hosting.org')
        self.assertEqual(instance.internal_lms_preview_domain, 'preview-pr234.sandbox.awesome.hosting.org')
        self.assertEqual(instance.internal_studio_domain, 'studio-pr234.sandbox.awesome.hosting.org')
        self.assertEqual(instance.edx_platform_repository_url, 'https://github.com/fork/repo.git')
        self.assertEqual(instance.edx_platform_commit, '7' * 40)
        self.assertEqual(instance.openedx_release, 'master')
        self.assertEqual(instance.configuration_extra_settings, ansible_extra_settings)
        self.assertEqual(instance.configuration_source_repo_url, 'https://github.com/open-craft/configuration')
        self.assertEqual(instance.configuration_version, 'named-release/elder')
        self.assertEqual(
            instance.name,
            'PR#234: Watched PR title which ... (bradenmacdonald) - fork/watch-branch (7777777)')

        # Also check the WatchedPullRequest object:
        watched_pr = WatchedPullRequest.objects.get(github_pr_url=pr_url)
        self.assertEqual(watched_pr.github_pr_number, 234)
        self.assertEqual(watched_pr.github_pr_url, 'https://github.com/source/repo/pull/234')
        self.assertEqual(watched_pr.github_base_url, 'https://github.com/fork/repo')
        self.assertEqual(watched_pr.branch_name, 'watch-branch')
        self.assertEqual(watched_pr.instance_id, instance.id)

        # Once the new instance/appserver has been spawned, it shouldn't spawn again:
        tasks.watch_pr()
        self.assertEqual(mock_spawn_appserver.call_count, 1)

    @patch('pr_watch.github.get_commit_id_from_ref')
    @patch('pr_watch.tasks.spawn_appserver')
    @patch('pr_watch.tasks.get_pr_list_from_usernames')
    @patch('pr_watch.tasks.get_username_list_from_team')
    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='awesome.hosting.org')
    def test_watch_pr_rate_limit_exceeded(
            self,
            mock_get_username_list,
            mock_get_pr_list_from_usernames,
            mock_spawn_appserver,
            mock_get_commit_id_from_ref
    ):
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
        pr_url = 'https://github.com/source/repo/pull/234'
        self.assertEqual(pr.github_pr_url, pr_url)
        mock_get_pr_list_from_usernames.side_effect = RateLimitExceeded
        mock_get_commit_id_from_ref.return_value = '7' * 40

        tasks.watch_pr()
        self.assertEqual(mock_spawn_appserver.call_count, 0)
