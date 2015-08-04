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

from unittest.mock import call, patch

from instance import repo
from instance.tests.base import TestCase


# Tests #######################################################################

class RepoTestCase(TestCase):
    """
    Test cases for Git repository helper functions
    """
    @patch('instance.repo.get_repo_from_url')
    def test_clone_configuration_repo(self, mock_get_repo_from_url):
        """
        Clone the configuration repository
        """
        mock_get_repo_from_url.return_value.create_remote.return_value.refs.opencraft = 'test-opencraft-ref'
        repo.clone_configuration_repo()
        self.assertEqual(mock_get_repo_from_url.mock_calls, [
            call('https://github.com/edx/configuration.git'),
            call().create_remote('opencraft', 'https://github.com/open-craft/configuration.git'),
            call().create_remote().fetch(),
            call().create_head('opencraft', 'test-opencraft-ref'),
            call().create_head().set_tracking_branch('test-opencraft-ref'),
            call().git.merge('opencraft')
        ])
