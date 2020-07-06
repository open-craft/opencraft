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
Git repository - Helper functions
"""

# Imports #####################################################################

import logging
from contextlib import contextmanager

import git

from instance import utils


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Functions ###################################################################

@contextmanager
def open_repository(repo_url, ref='master'):
    """
    Get a `Git` object for a repository URL and switch it to the reference `ref`.

    Note that this clones the repository locally.
    """
    with utils.create_temp_dir() as repo_dir_path:
        logger.info('Cloning repository %s (ref=%s) in %s...', repo_url, ref, repo_dir_path)

        # We can technically clone into a branch directly, but that wouldn't work for arbitrary references.
        repo = git.repo.base.Repo.clone_from(repo_url, repo_dir_path)
        repo.git.checkout(ref)
        repo.submodule_update()
        yield repo.git
