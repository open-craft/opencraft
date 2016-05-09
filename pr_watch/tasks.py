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
Worker tasks for development of Open edX
"""

# Imports #####################################################################

import logging

from django.conf import settings
from huey.contrib.djhuey import crontab, db_periodic_task

from pr_watch.github import get_username_list_from_team, get_pr_list_from_username
from pr_watch.models import WatchedPullRequest
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
    team_username_list = get_username_list_from_team(settings.WATCH_ORGANIZATION)

    for username in team_username_list:
        for pr in get_pr_list_from_username(username, settings.WATCH_FORK):
            instance, created = WatchedPullRequest.objects.update_or_create_from_pr(pr)
            if created:
                logger.info('New PR found, creating sandbox: %s', pr)
                spawn_appserver(instance.pk, mark_active_on_success=True, num_attempts=2)
