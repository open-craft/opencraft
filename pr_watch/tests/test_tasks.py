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
Worker tasks - Tests
"""

# Imports #####################################################################

import textwrap
from unittest.mock import patch
import yaml

from django.test import TestCase, override_settings

from userprofile.factories import make_user_and_organization

from pr_watch import tasks
from pr_watch.github import RateLimitExceeded
from pr_watch.models import WatchedPullRequest
from pr_watch.tests.factories import WatchedForkFactory, PRFactory


# Tests #######################################################################


class TasksTestCase(TestCase):
    """
    Test cases for PR Watcher worker tasks
    """
    @patch('pr_watch.github.get_commit_id_from_ref')
    @patch('pr_watch.tasks.create_new_deployment')
    @patch('pr_watch.tasks.get_pr_list_from_usernames')
    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='awesome.hosting.org')
    def test_watch_pr_new(self, mock_get_pr_list_from_usernames,
                          mock_create_new_deployment, mock_get_commit_id_from_ref):
        """
        New PR created on the watched repo
        """
        ansible_extra_settings = textwrap.dedent("""\
            WATCH: true
            edx_ansible_source_repo: https://github.com/open-craft/configuration
            configuration_version: named-release/elder
        """)
        _, organization = make_user_and_organization(github_username='bradenmacdonald')
        WatchedForkFactory(organization=organization, fork='source/repo')
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
        self.assertEqual(mock_create_new_deployment.call_count, 1)
        instance = mock_create_new_deployment.mock_calls[0][1][0]
        self.assertEqual(instance.internal_lms_domain, 'pr234.sandbox.awesome.hosting.org')
        self.assertEqual(instance.internal_lms_preview_domain, 'preview.pr234.sandbox.awesome.hosting.org')
        self.assertEqual(instance.internal_studio_domain, 'studio.pr234.sandbox.awesome.hosting.org')
        self.assertEqual(instance.edx_platform_repository_url, 'https://github.com/fork/repo.git')
        self.assertEqual(instance.edx_platform_commit, '7' * 40)
        self.assertEqual(instance.openedx_release, 'master')
        self.assertEqual(
            yaml.load(instance.configuration_extra_settings, Loader=yaml.SafeLoader),
            yaml.load(ansible_extra_settings, Loader=yaml.SafeLoader))
        self.assertEqual(instance.configuration_source_repo_url, 'https://github.com/open-craft/configuration')
        self.assertEqual(instance.configuration_version, 'named-release/elder')
        self.assertEqual(
            instance.name,
            'PR#234: Watched PR title which … (bradenmacdonald) - fork/watch-branch (7777777)')

        # Also check the WatchedPullRequest object:
        watched_pr = WatchedPullRequest.objects.get(github_pr_url=pr_url)
        self.assertEqual(watched_pr.github_pr_number, 234)
        self.assertEqual(watched_pr.github_pr_url, 'https://github.com/source/repo/pull/234')
        self.assertEqual(watched_pr.github_base_url, 'https://github.com/fork/repo')
        self.assertEqual(watched_pr.branch_name, 'watch-branch')
        self.assertEqual(watched_pr.instance_id, instance.id)

        # Once the new instance/appserver has been spawned, it shouldn't spawn again:
        tasks.watch_pr()
        self.assertEqual(mock_create_new_deployment.call_count, 1)

    @patch('pr_watch.github.get_commit_id_from_ref')
    @patch('pr_watch.tasks.create_new_deployment')
    @patch('pr_watch.tasks.get_pr_list_from_usernames')
    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='awesome.hosting.org')
    def test_watch_pr_rate_limit_exceeded(
            self,
            mock_get_pr_list_from_usernames,
            mock_create_new_deployment,
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
        self.assertEqual(mock_create_new_deployment.call_count, 0)

    @patch('pr_watch.github.get_commit_id_from_ref')
    @patch('pr_watch.tasks.create_new_deployment')
    @patch('pr_watch.tasks.get_pr_list_from_usernames')
    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='awesome.hosting.org')
    def test_watch_several_forks(self, mock_get_pr_list_from_usernames,
                                 mock_create_new_deployment, mock_get_commit_id_from_ref):
        """
        Create 2 watched forks with different settings, do a PR on each and check that both are seen and set up.
        """

        # Because we need to create 2 very similar repositories, we share code
        def create_test_data(number):
            """
            Return some data about a fork and repository. The data is almost the same, but values have a "1" or "2"
            (or the number you pass) appended. Also, the PR's id is 23001 for PR1, 23002 for PR2 etc.
            """
            pr_extra_settings = textwrap.dedent("""\
                PHRASE: "I am the value defined in PR{}"
                edx_ansible_source_repo: https://github.com/open-craft/configuration
                configuration_version: named-release/elder
            """.format(number))
            _, organization = make_user_and_organization(github_username='bradenmacdonald')
            wf = WatchedForkFactory(
                organization=organization,
                fork='source/repo{}'.format(number),
                # These 2 values will be replaced by the ones from the PR because the PR ones have more precedence
                configuration_source_repo_url='https://github.com/open-craft/configuration-fromwatchedfork',
                configuration_version='named-release/elder-fromwatchedfork',
                configuration_extra_settings=textwrap.dedent("""\
                PHRASE: "I am a setting which was set up the watched fork {number} (but will be overriden by the PR)"
                FORK_SPECIFIC_PHRASE: "I am another setting which was set up in watched fork {number}"
                """.format(number=number)),
                openedx_release='ginkgo.8',
            )
            pr_number = 23000 + number
            pr = PRFactory(
                number=pr_number,
                source_fork_name='fork/repo',
                target_fork_name=wf.fork,
                branch_name='watch-branch',
                title='Watched PR title which is very long',
                username='bradenmacdonald',
                body='Hello watcher!\n- - -\r\n**Settings**\r\n```\r\n{}```\r\nMore...'.format(
                    pr_extra_settings
                ),
            )
            pr_url = 'https://github.com/{}/pull/{}'.format(wf.fork, pr_number)
            pr_expected_resulting_settings = {
                'PHRASE': "I am the value defined in PR{}".format(number),
                'FORK_SPECIFIC_PHRASE': "I am another setting which was set up in watched fork {}".format(number),
                'edx_ansible_source_repo': 'https://github.com/open-craft/configuration',
                'configuration_version': 'named-release/elder',
            }

            return {'wf': wf, 'pr': pr, 'url': pr_url, 'expected_settings': pr_expected_resulting_settings}

        # Create 2 WatchedFork and 2 WatchedPullRequest (1 in each). They mostly use the same values except the first
        # one has values ending in "1" (e.g. source/repo1) and the 2nd in "2" (e.g. source/repo2)
        test_data = [
            create_test_data(1),
            create_test_data(2),
        ]

        def fake_pr_list_from_usernames(username_list, fork_name):
            """
            Simulate a GitHub answer to avoid doing API calls.
            When asked about PRs in the first repository, answer the first test PR,
            and when asked about the second, answer the second one.
            """
            if fork_name == 'openedx/edx-platform':
                return []
            elif fork_name == 'source/repo1':
                return [test_data[0]['pr']]  # first PR
            elif fork_name == 'source/repo2':
                return [test_data[1]['pr']]  # second PR
            else:
                raise NotImplementedError()

        # Substitute GitHub API calls by our results
        mock_get_pr_list_from_usernames.side_effect = fake_pr_list_from_usernames
        # Commit ID is the same in both PRs
        mock_get_commit_id_from_ref.return_value = '7' * 40

        self.assertEqual(mock_create_new_deployment.call_count, 0)

        # Check github (with our mocked response), this will detect 2 watched PRs and spawn 1 instance for each
        tasks.watch_pr()

        self.assertEqual(mock_create_new_deployment.call_count, 2)

        # Now do checks twice, once for every instance, checking the appropriate values each time
        for pr_number in [1, 2]:
            # "pr" contains the data we expect to see: URL, settings, and the PR object itself
            pr = test_data[pr_number - 1]

            instance = mock_create_new_deployment.mock_calls[pr_number - 1][1][0]
            subdomain_part = 'pr2300{}'.format(pr_number) # e.g. pr23001, pr23002, etc.
            self.assertEqual(instance.internal_lms_domain, '{}.sandbox.awesome.hosting.org'.format(subdomain_part))
            self.assertEqual(instance.internal_lms_preview_domain,
                             'preview.{}.sandbox.awesome.hosting.org'.format(subdomain_part))
            self.assertEqual(instance.internal_studio_domain,
                             'studio.{}.sandbox.awesome.hosting.org'.format(subdomain_part))
            self.assertEqual(instance.edx_platform_repository_url, 'https://github.com/fork/repo.git')
            self.assertEqual(instance.edx_platform_commit, '7' * 40)
            self.assertEqual(instance.openedx_release, 'ginkgo.8') # from WatchedFork
            self.assertEqual(
                yaml.load(instance.configuration_extra_settings, Loader=yaml.SafeLoader),
                pr['expected_settings'])
            # PR settings have precedence and they overwrote the ones in the WatchedFork
            self.assertEqual(instance.configuration_source_repo_url,
                             'https://github.com/open-craft/configuration')
            self.assertEqual(instance.configuration_version, 'named-release/elder')
            self.assertEqual(
                instance.name,
                'PR#2300{}: Watched PR title which … (bradenmacdonald) - '
                'fork/watch-branch (7777777)'.format(pr_number)
            )

            self.assertEqual(pr['pr'].github_pr_url, pr['url'])

            # Also check the WatchedPullRequest object:
            watched_pr = WatchedPullRequest.objects.get(github_pr_url=pr['url'])
            self.assertEqual(watched_pr.github_pr_number, 23000 + pr_number)
            self.assertEqual(watched_pr.github_pr_url, pr['url'])
            self.assertEqual(watched_pr.github_base_url, 'https://github.com/fork/repo')
            self.assertEqual(watched_pr.branch_name, 'watch-branch')
            self.assertEqual(watched_pr.instance_id, instance.id)

        # Once the new instance/appservers have been spawned, they shouldn't spawn again:
        tasks.watch_pr()
        self.assertEqual(mock_create_new_deployment.call_count, 2)

    @patch('pr_watch.github.get_commit_id_from_ref')
    @patch('pr_watch.tasks.create_new_deployment')
    @patch('pr_watch.tasks.get_pr_list_from_usernames')
    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='awesome.hosting.org')
    def test_disabled_watchedfork(self, mock_get_pr_list_from_usernames,
                                  mock_create_new_deployment, mock_get_commit_id_from_ref):
        """
        Creates WatchedFork with the 'enabled' field set to false and checks that its PRs are not watched.
        """

        ansible_extra_settings = textwrap.dedent("""\
            WATCH: true
            edx_ansible_source_repo: https://github.com/open-craft/configuration
            configuration_version: named-release/elder
        """)
        _, organization = make_user_and_organization()
        wf = WatchedForkFactory(
            organization=organization,
            fork='source/repo',
            enabled=False,
        )
        pr = PRFactory(
            number=234,
            source_fork_name='fork/repo',
            target_fork_name=wf.fork,
            branch_name='watch-branch',
            title='Watched PR title which is very long',
            username='bradenmacdonald',
            body='Hello watcher!\n- - -\r\n**Settings**\r\n```\r\n{}```\r\nMore...'.format(
                ansible_extra_settings
            ),
        )

        mock_get_commit_id_from_ref.return_value = '7' * 40
        mock_get_pr_list_from_usernames.return_value = [pr]

        tasks.watch_pr()
        self.assertEqual(mock_create_new_deployment.call_count, 0)
        self.assertEqual(WatchedPullRequest.objects.count(), 0)

    @patch('pr_watch.github.get_commit_id_from_ref')
    @patch('pr_watch.tasks.create_new_deployment')
    @patch('pr_watch.tasks.get_pr_list_from_usernames')
    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='awesome.hosting.org', WATCH_PRS=False)
    def test_watching_disabled(
            self, mock_get_pr_list_from_usernames, mock_create_new_deployment, mock_get_commit_id_from_ref,
    ):
        """
        Verifies that watch_pr exits early if WATCH_PRS is disabled.
        """
        tasks.watch_pr()
        mock_get_pr_list_from_usernames.assert_not_called()
        mock_create_new_deployment.assert_not_called()
        mock_get_commit_id_from_ref.assert_not_called()
