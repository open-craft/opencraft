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
Git repository - Tests
"""

# Imports #####################################################################

import os.path
from unittest.mock import call, patch

from instance import repo
from instance.tests.base import TestCase


# Tests #######################################################################

class RepoTestCase(TestCase):
    """
    Test cases for Git repository helper functions
    """
    @patch('git.Git')
    @patch('git.repo.base.Repo.clone_from')
    def test_open_repository(self, mock_clone_from, mock_git_class):
        """
        Get a repo object on a temporary directory
        """
        tmp_dir_path = None
        with repo.open_repository('http://example.com/repo.git', ref='test-branch') as mock_repo:
            tmp_dir_path = mock_clone_from.mock_calls[0][1][1]
            mock_clone_from.assert_called_once_with('http://example.com/repo.git', tmp_dir_path)
            self.assertTrue(os.path.isdir(tmp_dir_path))
            self.assertEqual(mock_repo.mock_calls, [call.checkout('test-branch')])
        self.assertFalse(os.path.isdir(tmp_dir_path))
