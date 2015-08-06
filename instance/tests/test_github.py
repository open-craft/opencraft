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

from mock import patch

from instance import github
from instance.tests.base import TestCase, get_raw_fixture


# Tests #######################################################################

class GitHubTestCase(TestCase):
    """
    Test cases for GitHub helper functions & API calls
    """
    def test_fork_name2tupe(self):
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

        self.assertEqual(
            github.get_pr_by_number('edx/edx-platform', 8474),
            github.PR(
                name='Add feature flag to allow hiding the discussion tab for individual courses. (smarnach)',
                body='**Description**\r\n\r\nHello!\nDesc with unicode «ταБЬℓσ»\r\n'
                     '- - -\r\n**Settings**\r\n```yaml\r\nEDXAPP_FEATURES:\r\n  ALLOW: true\r\n```',
                number=8474,
                fork_name='open-craft/edx-platform',
                branch_name='smarnach/hide-discussion-tab',
                extra_settings='EDXAPP_FEATURES:\r\n  ALLOW: true\r\n',
            )
        )

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
    def test_get_pr_list_for_user(self, mock_get_pr_by_number):
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
            github.get_pr_list_for_user('itsjeyd', 'edx/edx-platform'),
            [['edx/edx-platform', 9147], ['edx/edx-platform', 9146]]
        )

    @responses.activate
    @patch('instance.github.get_pr_list_for_user')
    def test_get_pr_list_for_organization_team(self, mock_get_pr_list_for_user):
        """
        Get list of open PR for team
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

        mock_get_pr_list_for_user.side_effect = lambda user_name, fork_name: [user_name, fork_name]

        self.assertEqual(
            github.get_pr_list_for_organization_team('open-craft', 'edx/edx-platform'),
            ['antoviaque', 'edx/edx-platform', 'bradenmacdonald', 'edx/edx-platform', 'e-kolpakov', 'edx/edx-platform',
             'itsjeyd', 'edx/edx-platform', 'Kelketek', 'edx/edx-platform', 'mtyaka', 'edx/edx-platform',
             'smarnach', 'edx/edx-platform']
        )

    @responses.activate
    def test_get_pr_list_for_organization_team_404(self):
        """
        Get list of open PR for non-existent team
        """
        responses.add(
            responses.GET, 'https://api.github.com/orgs/open-craft/teams',
            body=get_raw_fixture('github/api_teams.json'),
            content_type='application/json; charset=utf8',
            status=200)

        with self.assertRaises(KeyError, msg='non-existent'):
            github.get_pr_list_for_organization_team('open-craft', 'edx/edx-platform', team_name='non-existent')
