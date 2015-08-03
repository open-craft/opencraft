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
import responses

from django.test import TestCase
from instance.github import fork_name2tuple, get_commit_id_from_ref


# Tests #######################################################################

class GitHubTestCase(TestCase):
    """
    Test cases for GitHub helper functions & API calls
    """
    def test_fork_name2tupe(self):
        """
        Conversion of `fork_name` to `fork_tuple`
        """
        self.assertEqual(fork_name2tuple('open-craft/edx-platform'), ['open-craft', 'edx-platform'])

    @responses.activate
    def test_get_commit_id_from_ref(self):
        """
        Obtaining `commit_id` from a repo reference (eg. a branch)
        """
        responses.add(
            responses.GET, 'https://api.github.com/repos/edx/edx-platform/git/refs/heads/master',
            body=json.dumps({'object': {'sha': 'test-sha'}}),
            status=200)
        self.assertEqual(
            get_commit_id_from_ref('edx/edx-platform', 'master'),
            'test-sha')
