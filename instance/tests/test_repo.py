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
    @patch('git.repo.base.Repo.clone_from')
    def test_get_repo_from_url(self, mock_clone_from):
        """
        Get a repo object on a temporary dict
        """
        tmp_dir_path = None
        with repo.get_repo_from_url('http://example.com/repo.git'):
            tmp_dir_path = mock_clone_from.mock_calls[0][1][1]
            mock_clone_from.assert_called_once_with('http://example.com/repo.git', tmp_dir_path)
            self.assertTrue(os.path.isdir(tmp_dir_path))
        self.assertFalse(os.path.isdir(tmp_dir_path))

    @patch('instance.repo.get_repo_from_url')
    def test_clone_configuration_repo(self, mock_get_repo_from_url):
        """
        Clone the configuration repository
        """
        mock_configuration_repo = mock_get_repo_from_url.return_value.__enter__.return_value
        mock_configuration_repo.create_remote.return_value.refs.opencraft = 'test-opencraft-ref'
        mock_configuration_repo.working_dir = '/repo/tmp/dir'

        with repo.clone_configuration_repo() as configuration_repo_dir:
            self.assertEqual(configuration_repo_dir, '/repo/tmp/dir')

        mock_get_repo_from_url.assert_called_once_with('https://github.com/edx/configuration.git')
        self.assertEqual(mock_configuration_repo.mock_calls, [
            call.create_remote('opencraft', 'https://github.com/open-craft/configuration.git'),
            call.create_remote().fetch(),
            call.create_head('opencraft', 'test-opencraft-ref'),
            call.create_head().set_tracking_branch('test-opencraft-ref'),
            call.git.merge('opencraft')
        ])
