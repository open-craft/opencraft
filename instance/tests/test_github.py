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
GitHub - Tests
"""

# Imports #####################################################################

import json
import requests
import responses

from django.test.utils import override_settings

from mock import patch

from instance import github
from instance.tests.base import TestCase, get_raw_fixture


# Tests #######################################################################

class GitHubTestCase(TestCase):
    """
    Test cases for GitHub helper functions & API calls
    """
    def test_fork_name2tuple(self):
        """
        Conversion of `fork_name` to `fork_tuple`
        """
        self.assertEqual(github.fork_name2tuple('open-craft/edx-platform'), ['open-craft', 'edx-platform'])

    @responses.activate
    def test_get_commit_id_from_ref(self):
        """
        Obtaining `commit_id` from a repo reference (eg. a branch)
        """
        responses.add(
            responses.GET, 'https://api.github.com/repos/edx/edx-platform/git/refs/heads/master',
            body=json.dumps({'object': {'sha': 'test-sha'}}),
            content_type='application/json; charset=utf8',
            status=200)
        self.assertEqual(
            github.get_commit_id_from_ref('edx/edx-platform', 'master'),
            'test-sha')

    def test_get_settings_from_pr_body(self):
        """
        Extract settings from a string containing settings
        """
        settings_str = 'TEST: true\r\nother: false\r\n'
        pr_body = "Description\r\nover\r\nlines\r\n- - -\r\n**Settings**\r\n```yaml\r\n" + settings_str + "```"
        self.assertEqual(github.get_settings_from_pr_body(pr_body), settings_str)

    def test_get_settings_from_pr_body_not_contain(self):
        """
        Extract settings from a string which doesn't contain settings
        """
        pr_body = "Description\r\nover\r\nlines\r\n- - -\r\n**Settings**\r\nMALFORMED"
        self.assertEqual(github.get_settings_from_pr_body(pr_body), '')

    @responses.activate
    def test_get_pr_by_number(self):
        """
        Get PR object for existing PR number
        """
        responses.add(
            responses.GET, 'https://api.github.com/repos/edx/edx-platform/pulls/8474',
            body=get_raw_fixture('github/api_pr.json'),
            content_type='application/json; charset=utf8',
            status=200)

        pr = github.get_pr_by_number('edx/edx-platform', 8474)
        self.assertEqual(
            pr.title,
            'Add feature flag to allow hiding the discussion tab for individual courses.')
        self.assertEqual(
            pr.body,
            '**Description**\r\n\r\nHello!\nDesc with unicode «ταБЬℓσ»\r\n'
            '- - -\r\n**Settings**\r\n```yaml\r\nEDXAPP_FEATURES:\r\n  ALLOW: true\r\n```')
        self.assertEqual(pr.number, 8474)
        self.assertEqual(pr.fork_name, 'open-craft/edx-platform')
        self.assertEqual(pr.branch_name, 'smarnach/hide-discussion-tab')
        self.assertEqual(pr.extra_settings, 'EDXAPP_FEATURES:\r\n  ALLOW: true\r\n')
        self.assertEqual(pr.username, 'smarnach')

    @responses.activate
    def test_get_pr_by_number_404(self):
        """
        Get PR object for non-existing PR
        """
        responses.add(
            responses.GET, 'https://api.github.com/repos/edx/edx-platform/pulls/1234567890',
            body=json.dumps({'message': 'Not Found'}),
            content_type='application/json; charset=utf8',
            status=404)

        with self.assertRaises(requests.exceptions.HTTPError) as cm:
            github.get_pr_by_number('edx/edx-platform', 1234567890)
        self.assertEqual(cm.exception.response.status_code, 404)

    @responses.activate
    @patch('instance.github.get_pr_by_number')
    def test_get_pr_list_from_username(self, mock_get_pr_by_number):
        """
        Get list of open PR for user
        """
        responses.add(
            responses.GET, 'https://api.github.com/search/issues?sort=created'
                           '&q=is:open is:pr author:itsjeyd repo:edx/edx-platform',
            match_querystring=True,
            body=get_raw_fixture('github/api_search_open_prs_user.json'),
            content_type='application/json; charset=utf8',
            status=200)

        mock_get_pr_by_number.side_effect = lambda fork_name, pr_number: [fork_name, pr_number]

        self.assertEqual(
            github.get_pr_list_from_username('itsjeyd', 'edx/edx-platform'),
            [['edx/edx-platform', 9147], ['edx/edx-platform', 9146]]
        )

    @override_settings(WATCH_ORGANIZATION=None, WATCH_USER="luckyluke")
    def test_get_watched_users(self):
        """
        Get the list of watched users
        """
        self.assertEqual(['luckyluke'], github.get_watched_usernames())

    @responses.activate
    def test_get_username_list_from_team(self):
        """
        Get list of members in a team
        """
        responses.add(
            responses.GET, 'https://api.github.com/orgs/open-craft/teams',
            body=get_raw_fixture('github/api_teams.json'),
            content_type='application/json; charset=utf8',
            status=200)
        responses.add(
            responses.GET, 'https://api.github.com/teams/799617/members',
            body=get_raw_fixture('github/api_members.json'),
            content_type='application/json; charset=utf8',
            status=200)

        self.assertEqual(
            github.get_username_list_from_team('open-craft'),
            ['antoviaque', 'bradenmacdonald', 'e-kolpakov', 'itsjeyd', 'Kelketek', 'mtyaka', 'smarnach']
        )

    @responses.activate
    def test_get_username_list_from_team_404(self):
        """
        Get list of open PR for non-existent team
        """
        responses.add(
            responses.GET, 'https://api.github.com/orgs/open-craft/teams',
            body=get_raw_fixture('github/api_teams.json'),
            content_type='application/json; charset=utf8',
            status=200)

        with self.assertRaises(KeyError, msg='non-existent'):
            github.get_username_list_from_team('open-craft', team_name='non-existent')

    def test_use_continuous_provisioning_none(self):
        """
        PR doesn't specify if continuous provisioning should be provided or not - return None
        """
        pr = github.PR("number", "fork_name", "branch_name", "title", "username", body='some body')
        self.assertEqual(pr.use_continuous_provisioning('ci.example.com'), None)

    def test_use_continuous_reprovisioning_true(self):
        """
        PR specifies that continuous provisioning should be provided - return True
        """
        pr = github.PR("number", "fork_name", "branch_name", "title", "username",
                       body='some body\nci.example.com (continuously provisioned)')
        self.assertEqual(pr.use_continuous_provisioning('ci.example.com'), True)
        self.assertEqual(pr.use_continuous_provisioning('other.example.com'), None)

    def test_use_continuous_reprovisioning_false(self):
        """
        PR specifies that reprovisioning should be manual - return False
        """
        pr = github.PR("number", "fork_name", "branch_name", "title", "username",
                       body='some body\nci.example.com (manually reprovisioned)')
        self.assertEqual(pr.use_continuous_provisioning('ci.example.com'), False)
        self.assertEqual(pr.use_continuous_provisioning('other.example.com'), None)
