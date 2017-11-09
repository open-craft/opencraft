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
Tests for the WatchedPullRequest model and manager
"""

# Imports #####################################################################

import textwrap
from unittest.mock import call, patch
import yaml

from django.test import TestCase, override_settings

from pr_watch.models import WatchedPullRequest
from pr_watch.tests.factories import PRFactory, WatchedForkFactory


# Tests #######################################################################

class WatchedPullRequestTestCase(TestCase):
    """
    Test cases for WatchedPullRequest model and manager
    """
    def setUp(self):
        """
        Mock the 'get_commit_id_from_ref' method so it doesn't make a GitHub API call
        """
        super().setUp()
        patcher = patch('pr_watch.models.github.get_commit_id_from_ref')
        self.addCleanup(patcher.stop)
        self.mock_get_commit_id_from_ref = patcher.start()
        self.mock_get_commit_id_from_ref.return_value = '9' * 40

    def test_get_by_fork_name(self):
        """
        Use `fork_name` to get an instance object from the ORM
        """
        watched_fork = WatchedForkFactory(organization='get-by', fork='fork-name')
        WatchedPullRequest.objects.create(
            github_organization_name='get-by',
            github_repository_name='fork-name',
            watched_fork=watched_fork,
        )
        watched_pr = WatchedPullRequest.objects.get(fork_name='get-by/fork-name')
        self.assertEqual(watched_pr.fork_name, 'get-by/fork-name')

    def test_github_attributes(self):
        """
        GitHub-specific WatchedPullRequest attributes
        """
        watched_pr = WatchedPullRequest(
            github_organization_name='open-craft',
            github_pr_url='https://github.com/edx/edx-dest/pull/234',
            github_repository_name='edx',
            branch_name='test-branch',
        )
        self.assertEqual(watched_pr.fork_name, 'open-craft/edx')
        self.assertEqual(watched_pr.target_fork_name, 'edx/edx-dest')
        self.assertEqual(watched_pr.github_base_url, 'https://github.com/open-craft/edx')
        self.assertEqual(watched_pr.github_pr_number, 234)
        self.assertEqual(watched_pr.github_branch_url, 'https://github.com/open-craft/edx/tree/test-branch')
        self.assertEqual(watched_pr.repository_url, 'https://github.com/open-craft/edx.git')
        self.assertEqual(watched_pr.updates_feed, 'https://github.com/open-craft/edx/commits/test-branch.atom')

    def test_set_fork_name(self):
        """
        Set org & repo using the fork name
        """
        watched_fork = WatchedForkFactory(organization='org2', fork='some-name')
        watched_pr = WatchedPullRequest(watched_fork=watched_fork)
        watched_pr.set_fork_name('org2/another-repo')
        self.assertEqual(watched_pr.github_organization_name, 'org2')
        self.assertEqual(watched_pr.github_repository_name, 'another-repo')
        watched_pr.save()

        # Check values in DB
        watched_pr = WatchedPullRequest.objects.get(pk=watched_pr.pk)
        self.assertEqual(watched_pr.github_organization_name, 'org2')
        self.assertEqual(watched_pr.github_repository_name, 'another-repo')

    def test_get_branch_tip(self):
        """
        Set the commit id to the tip of the current branch, using the default commit policy (True)
        """
        self.mock_get_commit_id_from_ref.return_value = 'b' * 40
        watched_pr = WatchedPullRequest(
            github_organization_name='org3',
            github_repository_name='repo3',
        )
        self.assertEqual(watched_pr.get_branch_tip(), 'b' * 40)
        self.assertEqual(self.mock_get_commit_id_from_ref.mock_calls, [
            call('org3/repo3', 'master', ref_type='heads'),
        ])

    def test_get_branch_tip_with_tag(self):
        """
        Set the commit id to a tag.

        TODO: Is this 'ref_type' code used for anything?
        """
        self.mock_get_commit_id_from_ref.return_value = 'c' * 40
        watched_fork = WatchedForkFactory(fork='org9/repo')
        instance = WatchedPullRequest.objects.create(
            fork_name='org9/repo',
            branch_name='new-tag',
            ref_type='tag',
            watched_fork=watched_fork
        )
        self.assertEqual(instance.get_branch_tip(), 'c' * 40)
        self.assertEqual(self.mock_get_commit_id_from_ref.mock_calls, [
            call('org9/repo', 'new-tag', ref_type='tag'),
        ])
        self.assertEqual(instance.branch_name, 'new-tag')
        self.assertEqual(instance.ref_type, 'tag')

    @override_settings(
        INSTANCE_EPHEMERAL_DATABASES=True,
        DEFAULT_INSTANCE_BASE_DOMAIN='basedomain.com',
        DEFAULT_LMS_PREVIEW_DOMAIN_PREFIX='lms-preview.',
        DEFAULT_STUDIO_DOMAIN_PREFIX='studio-'
    )
    def test_create_from_pr(self):
        """
        Create an instance from a pull request
        """
        pr = PRFactory()
        watched_fork = WatchedForkFactory(fork=pr.fork_name)
        instance, created = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
        self.assertTrue(created)

        watched_pr = instance.watchedpullrequest
        self.assertEqual(watched_pr.instance, instance)
        self.assertEqual(watched_pr.github_pr_number, pr.number)
        self.assertEqual(watched_pr.fork_name, pr.fork_name)
        self.assertEqual(watched_pr.branch_name, pr.branch_name)

        internal_lms_domain = 'pr{}.sandbox.basedomain.com'.format(pr.number)
        self.assertEqual(instance.internal_lms_domain, internal_lms_domain)
        self.assertEqual(instance.internal_lms_preview_domain, 'lms-preview.{}'.format(internal_lms_domain))
        self.assertEqual(instance.internal_studio_domain, 'studio-{}'.format(internal_lms_domain))
        self.assertRegex(instance.name, r'^PR')
        self.assertEqual(instance.edx_platform_commit, '9' * 40)
        self.assertTrue(instance.use_ephemeral_databases)

        same_instance, created = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
        self.assertEqual(instance, same_instance)
        self.assertFalse(created)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=False)
    def test_create_from_pr_ephemeral_databases(self):
        """
        Instances should use ephemeral databases if requested in the PR
        """
        pr = PRFactory(body='pr123.sandbox.example.com (ephemeral databases)', number=123)
        watched_fork = WatchedForkFactory(fork=pr.fork_name)
        instance, _ = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
        self.assertTrue(instance.use_ephemeral_databases)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=True)
    def test_create_from_pr_persistent_databases(self):
        """
        Instances should use persistent databases if requested in the PR
        """
        pr = PRFactory(body='pr123.sandbox.example.com (persistent databases)', number=123)
        watched_fork = WatchedForkFactory(fork=pr.fork_name)
        instance, _ = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
        self.assertFalse(instance.use_ephemeral_databases)

    def test_create_from_pr_and_watchedfork_values(self):
        """
        Create an instance from a pull request, and check that the default values from the watched fork are used.
        """
        pr = PRFactory()
        watched_fork = WatchedForkFactory(
            fork=pr.fork_name,
            configuration_source_repo_url='https://github.com/open-craft/configuration-fromwatchedfork',
            configuration_version='named-release/elder-fromwatchedfork',
            configuration_extra_settings=textwrap.dedent("""\
                PHRASE: "Hello"
                """),
            openedx_release='ginkgo.8',
        )
        instance, created = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
        self.assertTrue(created)

        self.assertEqual(instance.configuration_source_repo_url,
                         'https://github.com/open-craft/configuration-fromwatchedfork')
        self.assertEqual(instance.configuration_version,
                         'named-release/elder-fromwatchedfork')
        self.assertEqual(instance.openedx_release, 'ginkgo.8')
        self.assertEqual(yaml.load(instance.configuration_extra_settings), {'PHRASE': 'Hello'})
