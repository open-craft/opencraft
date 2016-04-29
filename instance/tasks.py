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
Worker tasks for instance hosting & management
"""

# Imports #####################################################################

from huey.djhuey import crontab, db_periodic_task, db_task

from django.conf import settings

from instance.github import get_username_list_from_team, get_pr_list_from_username
from instance.models.instance import SingleVMOpenEdXInstance


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Tasks #######################################################################

@db_task()
def provision_instance(instance_pk):
    """
    Run provisioning on an existing instance
    """
    logger.info('Retreiving instance: pk=%s', instance_pk)
    instance = SingleVMOpenEdXInstance.objects.get(pk=instance_pk)

    logger.info('Running provisioning on %s', instance)
    instance.provision()


@db_periodic_task(crontab(minute='*/1'))
def watch_pr():
    """
    Automatically create/update sandboxes for PRs opened by members of the watched
    organization on the watched repository
    """
    team_username_list = get_username_list_from_team(settings.WATCH_ORGANIZATION)

    for username in team_username_list:
        for pr in get_pr_list_from_username(username, settings.WATCH_FORK):
            sub_domain = 'pr{number}.sandbox'.format(number=pr.number)
            instance, created = SingleVMOpenEdXInstance.objects.update_or_create_from_pr(pr, sub_domain)
            if created:
                logger.info('New PR found, creating sandbox: %s', pr)
                provision_instance(instance.pk)
