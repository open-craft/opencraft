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
Git repository - Helper functions
"""

# Imports #####################################################################

import git
import tempfile
import shutil

from contextlib import contextmanager


# Functions ###################################################################

@contextmanager
def get_repo_from_url(repo_url):
    """
    Get a `Repo` object from a repository URL

    Note that this clones the repository locally
    """
    repo_dir_path = tempfile.mkdtemp()
    yield git.repo.base.Repo.clone_from(repo_url, repo_dir_path)
    shutil.rmtree(repo_dir_path)


@contextmanager
def clone_configuration_repo():
    """
    Clone the configuration repository, including patches to get it to work with OpenStack

    Returns the path to the directory where the repository has been cloned
    """
    # Cloning & remotes
    with get_repo_from_url('https://github.com/edx/configuration.git') as configuration_repo:
        opencraft_remote = configuration_repo.create_remote('opencraft',
                                                            'https://github.com/open-craft/configuration.git')
        opencraft_remote.fetch()

        # Merge the opencraft branch, which contains fixes to get the ansible scripts to run in our
        # specific case, for example openstack fixes - it should be kept to a minimum and pushed upstream
        opencraft_branch = configuration_repo.create_head('opencraft', opencraft_remote.refs.opencraft)
        opencraft_branch.set_tracking_branch(opencraft_remote.refs.opencraft)
        configuration_repo.git.merge('opencraft')

        yield configuration_repo.working_dir
