# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Worker tasks for development of Open edX
"""

# Imports #####################################################################

import logging

from huey.api import crontab
from huey.contrib.djhuey import db_periodic_task

from userprofile.models import UserProfile

from pr_watch.github import (
    get_pr_list_from_usernames,
    RateLimitExceeded
)
from pr_watch.models import WatchedFork, WatchedPullRequest

from instance.models.openedx_appserver import Source
from instance.tasks import spawn_appserver


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Tasks #######################################################################

@db_periodic_task(crontab(minute='*/1'))
def watch_pr():
    """
    Automatically create sandboxes for PRs opened by members of the watched
    organization on the watched repository
    """
    try:
        for watched_fork in WatchedFork.objects.filter(enabled=True):
            usernames = list(
                UserProfile.objects.filter(
                    organization=watched_fork.organization,
                ).exclude(
                    github_username__isnull=True,
                ).values_list(
                    'github_username',
                    flat=True
                )
            )
            for pr in get_pr_list_from_usernames(usernames, watched_fork.fork):
                instance, created = WatchedPullRequest.objects.get_or_create_from_pr(pr, watched_fork)
                if created:
                    logger.info('New PR found, creating sandbox: %s', pr)
                    # TODO: set fail_emails from pr username
                    spawn_appserver(instance.ref.pk, mark_active_on_success=True,
                                    num_attempts=2, source=Source.WATCHED_PR)
    except RateLimitExceeded as err:
        logger.warning('Could not complete PR scan due to an error: %s', str(err))
