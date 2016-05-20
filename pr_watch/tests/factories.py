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
Test factory: PR (Github pull request)
"""

# Imports #####################################################################

from unittest.mock import patch

import factory

from pr_watch import github
from pr_watch.models import WatchedPullRequest


# Classes #####################################################################

class PRFactory(factory.Factory):
    """
    Factory for PR instances
    """
    class Meta:
        model = github.PR

    number = factory.Sequence(int)
    source_fork_name = 'fork/repo'
    target_fork_name = 'source/repo'
    branch_name = 'master'
    title = factory.Sequence('PR #{}'.format)
    username = 'edx'
    body = ''

# Functions ###################################################################


def make_watched_pr_and_instance(**kwargs):
    """
    Create a WatchedPullRequest and associated OpenEdXInstance
    """
    pr = PRFactory(**kwargs)
    with patch('pr_watch.github.get_commit_id_from_ref', return_value=('5' * 40)):
        instance, dummy = WatchedPullRequest.objects.get_or_create_from_pr(pr)
    return instance.watchedpullrequest
