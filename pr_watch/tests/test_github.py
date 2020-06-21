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
GitHub - Tests
"""

# Imports #####################################################################

from datetime import datetime, timedelta
import json
from unittest.mock import patch

from django.test import TestCase
import responses

from instance.tests.base import get_raw_fixture
from pr_watch import github


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

    @responses.activate
    def test_get_commit_id_from_ref_404(self):
        """
        Attempt to fetch a branch that has been deleted
        """
        responses.add(
            responses.GET, 'https://api.github.com/repos/edx/edx-platform/git/refs/heads/deleted-branch',
            body=json.dumps({'message': 'Not Found'}),
            content_type='application/json; charset=utf8',
            status=404)

        with self.assertRaises(github.ObjectDoesNotExist):
            github.get_commit_id_from_ref('edx/edx-platform', 'deleted-branch')

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
    def test_get_pr_info_by_number(self):
        """
        Get all available information about PR by PR number
        """
        pr_fixture = get_raw_fixture('github/api_pr.json')
        responses.add(
            responses.GET, 'https://api.github.com/repos/edx/edx-platform/pulls/8474',
            body=pr_fixture,
            content_type='application/json; charset=utf8',
            status=200
        )
        pr_info = github.get_pr_info_by_number('edx/edx-platform', 8474)
        expected_pr_info = json.loads(pr_fixture)
        self.assertEqual(pr_info, expected_pr_info)

    @responses.activate
    def test_get_pr_by_number(self):
        """
        Get PR object for existing PR number
        """
        responses.add(
            responses.GET, 'https://api.github.com/repos/edx/edx-platform/pulls/8474',
            body=get_raw_fixture('github/api_pr.json'),
            content_type='application/json; charset=utf8',
            status=200
        )

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
        self.assertEqual(pr.repo_name, 'edx/edx-platform')
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

        with self.assertRaises(github.ObjectDoesNotExist):
            github.get_pr_by_number('edx/edx-platform', 1234567890)

    @responses.activate
    @patch('pr_watch.github.get_pr_by_number')
    def test_get_pr_list_from_username(self, mock_get_pr_by_number):
        """
        Get list of open PR for user
        """
        last_hour_dt = (datetime.today() - timedelta(hours=1)).date()
        responses.add(
            responses.GET, 'https://api.github.com/search/issues?sort=created&q=is:open '
                           'is:pr author:itsjeyd repo:edx/edx-platform created:>{}'.format(last_hour_dt),
            match_querystring=True,
            body=get_raw_fixture('github/api_search_open_prs_user.json'),
            content_type='application/json; charset=utf8',
            status=200,
        )

        mock_get_pr_by_number.side_effect = lambda fork_name, pr_number: [fork_name, pr_number]

        self.assertEqual(
            github.get_pr_list_from_username('itsjeyd', 'edx/edx-platform'),
            [['edx/edx-platform', 9147], ['edx/edx-platform', 9146]]
        )

    @responses.activate
    @patch('pr_watch.github.get_pr_by_number')
    def test_get_pr_list_from_usernames(self, mock_get_pr_by_number):
        """
        Get list of open PR for a list of users
        """
        # Verify we get no PRs when invoking the function with an empty username list.
        self.assertEqual(github.get_pr_list_from_usernames([], 'edx/edx-platform'), [])

        last_hour_dt = (datetime.today() - timedelta(hours=1)).date()
        responses.add(
            responses.GET, 'https://api.github.com/search/issues?sort=created&q=is:open '
                           'is:pr author:itsjeyd author:haikuginger repo:edx/edx-platform '
                           'created:>{}'.format(last_hour_dt),
            match_querystring=True,
            body=get_raw_fixture('github/api_search_open_prs_multiple_users.json'),
            content_type='application/json; charset=utf8',
            status=200)

        mock_get_pr_by_number.side_effect = lambda fork_name, pr_number: [fork_name, pr_number]

        print(github.get_pr_list_from_usernames(['itsjeyd', 'haikuginger'], 'edx/edx-platform'))
        self.assertEqual(
            github.get_pr_list_from_usernames(['itsjeyd', 'haikuginger'], 'edx/edx-platform'),
            [['edx/edx-platform', 9147], ['edx/edx-platform', 9146], ['edx/edx-platform', 15921]]
        )

    def test_parse_date(self):
        """
        Parse string representing date in ISO 8601 format (as returned by GitHub).
        """
        date = github.parse_date("2016-10-11T15:10:30Z")
        self.assertIsInstance(date, datetime)
        self.assertEqual(date.year, 2016)
        self.assertEqual(date.month, 10)
        self.assertEqual(date.day, 11)
        self.assertEqual(date.hour, 15)
        self.assertEqual(date.minute, 10)
        self.assertEqual(date.second, 30)
