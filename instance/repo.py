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

from git.repo.base import Repo
from tempfile import mkdtemp


# Functions ###################################################################

def get_repo_from_url(repo_url):
    # TODO: Delete the temporary directory after use
    return Repo.clone_from(repo_url, mkdtemp())

def clone_configuration_repo():
    # Cloning & remotes
    configuration_repo = get_repo_from_url('https://github.com/edx/configuration.git')
    opencraft_remote = configuration_repo.create_remote('opencraft',
                                                        'https://github.com/open-craft/configuration.git')
    opencraft_remote.fetch()

    # Merge the opencraft branch, which contains fixes to get the ansible scripts to run in our 
    # specific case, for example openstack fixes - it should be kept to a minimum and pushed upstream
    opencraft_branch = configuration_repo.create_head('opencraft', opencraft_remote.refs.opencraft)
    opencraft_branch.set_tracking_branch(opencraft_remote.refs.opencraft)
    configuration_repo.git.merge('opencraft')

    return configuration_repo.working_dir
