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
Tests for the WatchedPullRequest model and manager
"""

# Imports #####################################################################

import json
import textwrap
from unittest.mock import call, patch

import ddt
from django.db import IntegrityError
from django.test import TestCase, override_settings
import yaml

from pr_watch.models import WatchedPullRequest
from pr_watch.tests.factories import PRFactory, WatchedForkFactory
from userprofile.factories import make_user_and_organization


# Tests #######################################################################

@ddt.ddt
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
        _, self.organization = make_user_and_organization()

    def test_get_by_fork_name(self):
        """
        Use `fork_name` to get an instance object from the ORM
        """
        _, organization = make_user_and_organization(org_name="Get by", org_handle="get-by")
        watched_fork = WatchedForkFactory(organization=organization, fork='fork-name')
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
            github_pr_url='https://github.com/openedx/edx-dest/pull/234',
            github_repository_name='openedx',
            branch_name='test-branch',
        )
        self.assertEqual(watched_pr.fork_name, 'open-craft/openedx')
        self.assertEqual(watched_pr.target_fork_name, 'openedx/edx-dest')
        self.assertEqual(watched_pr.github_base_url, 'https://github.com/open-craft/openedx')
        self.assertEqual(watched_pr.github_pr_number, 234)
        self.assertEqual(watched_pr.github_branch_url, 'https://github.com/open-craft/openedx/tree/test-branch')
        self.assertEqual(watched_pr.repository_url, 'https://github.com/open-craft/openedx.git')
        self.assertEqual(watched_pr.updates_feed, 'https://github.com/open-craft/openedx/commits/test-branch.atom')

    def test_set_fork_name(self):
        """
        Set org & repo using the fork name
        """
        _, organization = make_user_and_organization(org_name="Org2", org_handle="org2")
        watched_fork = WatchedForkFactory(organization=organization, fork='some-name')
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
        _, organization = make_user_and_organization(org_name="Org9", org_handle="org9")
        watched_fork = WatchedForkFactory(organization=organization, fork='org9/repo')
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
        DEFAULT_INSTANCE_BASE_DOMAIN='basedomain.com',
        DEFAULT_LMS_PREVIEW_DOMAIN_PREFIX='lms-preview.',
        DEFAULT_STUDIO_DOMAIN_PREFIX='studio-'
    )
    @patch(
        'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @ddt.data(True, False)
    def test_create_from_pr(self, use_watched_fork, mock_consul):
        """
        Create an instance from a pull request
        """
        pr = PRFactory()
        _, organization = make_user_and_organization()
        if use_watched_fork:
            watched_fork = WatchedForkFactory(fork=pr.fork_name, organization=organization)
            domain_prefix = ''
            name_prefix = ''
        else:
            watched_fork = None
            domain_prefix = 'ext'
            name_prefix = 'EXT'

        instance, created = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
        self.assertTrue(created)

        watched_pr = instance.watchedpullrequest
        self.assertEqual(watched_pr.instance, instance)
        self.assertEqual(watched_pr.github_pr_number, pr.number)
        self.assertEqual(watched_pr.fork_name, pr.fork_name)
        self.assertEqual(watched_pr.branch_name, pr.branch_name)

        internal_lms_domain = '{}pr{}.sandbox.basedomain.com'.format(domain_prefix, pr.number)
        self.assertEqual(instance.internal_lms_domain, internal_lms_domain)
        self.assertEqual(instance.internal_lms_preview_domain, 'lms-preview.{}'.format(internal_lms_domain))
        self.assertEqual(instance.internal_studio_domain, 'studio-{}'.format(internal_lms_domain))
        self.assertRegex(instance.name, r'^{}PR'.format(name_prefix))
        self.assertEqual(instance.edx_platform_commit, '9' * 40)
        same_instance, created = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
        self.assertEqual(instance, same_instance)
        self.assertFalse(created)

    def test_create_from_pr_and_watchedfork_values(self):
        """
        Create an instance from a pull request, and check that the default values from the watched fork are used.
        """
        pr = PRFactory()
        _, organization = make_user_and_organization()
        watched_fork = WatchedForkFactory(
            fork=pr.fork_name,
            organization=organization,
            ansible_appserver_repo_url='https://github.com/open-craft/ansible-playbooks.git',
            ansible_appserver_playbook='playbooks/appserver.yml',
            ansible_appserver_requirements_path='requirements.txt',
            ansible_appserver_version='ansible2.8.17',
            openstack_server_base_image='{"name_or_id":"focal-20.04-unmodified"}',
            configuration_source_repo_url='https://github.com/open-craft/configuration-fromwatchedfork',
            configuration_version='named-release/elder-fromwatchedfork',
            configuration_extra_settings=textwrap.dedent("""\
                PHRASE: "Hello"
                """),
            openedx_release='ginkgo.8',
        )
        with patch(
                'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
                return_value=(1, True)
        ):
            instance, created = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
        self.assertTrue(created)

        self.assertEqual(instance.ansible_appserver_repo_url, 'https://github.com/open-craft/ansible-playbooks.git')
        self.assertEqual(instance.ansible_appserver_playbook, 'playbooks/appserver.yml')
        self.assertEqual(instance.ansible_appserver_requirements_path, 'requirements.txt')
        self.assertEqual(instance.ansible_appserver_version, 'ansible2.8.17')
        self.assertEqual(json.loads(instance.openstack_server_base_image), {"name_or_id":"focal-20.04-unmodified"})

        self.assertEqual(instance.configuration_source_repo_url,
                         'https://github.com/open-craft/configuration-fromwatchedfork')
        self.assertEqual(instance.configuration_version,
                         'named-release/elder-fromwatchedfork')
        self.assertEqual(instance.openedx_release, 'ginkgo.8')
        self.assertEqual(yaml.load(instance.configuration_extra_settings, Loader=yaml.SafeLoader), {'PHRASE': 'Hello'})

    def test_unique_constraints(self):
        """
        Verifies that we cannot create multiple database entries for following a specific pull request.
        """
        pr = PRFactory()
        _, organization = make_user_and_organization()
        watched_fork = WatchedForkFactory(
            fork=pr.fork_name,
            organization=organization,
            configuration_source_repo_url='https://github.com/open-craft/configuration-fromwatchedfork',
        )
        WatchedPullRequest.objects.create(
            github_organization_name='get-by',
            github_repository_name='fork-name',
            branch_name='test',
            github_pr_url='https://github.com/open-craft/opencraft/pull/123/',
            watched_fork=watched_fork,
        )
        self.assertRaises(
            IntegrityError,
            WatchedPullRequest.objects.create,
            github_organization_name='get-by',
            github_repository_name='fork-name',
            branch_name='test',
            github_pr_url='https://github.com/open-craft/opencraft/pull/123/',
            watched_fork=watched_fork,
        )

    def test_unique_constraints_allow_multiple_per_branch(self):
        """
        Verifies that the unique constraint on a pull request allows for multiple copies of the same branch,
        but different URLs.
        """
        pr = PRFactory()
        _, organization = make_user_and_organization()
        watched_fork = WatchedForkFactory(
            fork=pr.fork_name,
            organization=organization,
            configuration_source_repo_url='https://github.com/open-craft/configuration-fromwatchedfork',
        )
        watched_pr1 = WatchedPullRequest.objects.create(
            github_organization_name='get-by',
            github_repository_name='fork-name',
            branch_name='test',
            github_pr_url='https://github.com/open-craft/opencraft/pull/123/',
            watched_fork=watched_fork,
        )
        watched_pr2 = WatchedPullRequest.objects.create(
            github_organization_name='get-by',
            github_repository_name='fork-name',
            branch_name='test',
            github_pr_url='https://github.com/open-craft/opencraft/pull/1234/',
            watched_fork=watched_fork,
        )
        self.assertNotEqual(watched_pr1, watched_pr2)
