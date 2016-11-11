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
Worker tasks for instance hosting & management
"""

# Imports #####################################################################

from datetime import datetime
import logging

from huey.contrib.djhuey import crontab, db_task, db_periodic_task

from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance
from instance.utils import sufficient_time_passed
from pr_watch import github


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Tasks #######################################################################

@db_task()
def spawn_appserver(instance_ref_id, mark_active_on_success=False, num_attempts=1):
    """
    Create a new AppServer for an existing instance.

    instance_ref_id should be the ID of an InstanceReference (instance.ref.pk)

    Optionally mark the new AppServer as active when the provisioning completes.
    Optionally retry up to 'num_attempts' times
    """
    for i in range(1, num_attempts + 1):
        logger.info('Retrieving instance: ID=%s', instance_ref_id)
        # Fetch the instance inside the loop, in case it has been updated
        instance = OpenEdXInstance.objects.get(ref_set__pk=instance_ref_id)

        instance.logger.info('Spawning new AppServer, attempt %d of %d', i, num_attempts)
        appserver_id = instance.spawn_appserver()
        if appserver_id:
            if mark_active_on_success:
                # If the AppServer provisioned successfully, make it the active one:
                # Note: if I call spawn_appserver() twice, and the second one provisions sooner, the first one may then
                # finish and replace the second as the active server. We are not really worried about that for now.
                instance.set_appserver_active(appserver_id)
            break


@db_task()
def set_appserver_active(appserver_id):
    """
    Mark an AppServer as active.
    """
    logger.info('Retrieving AppServer: ID=%s', appserver_id)
    appserver = OpenEdXAppServer.objects.get(pk=appserver_id)
    appserver.instance.set_appserver_active(appserver_id)


@db_task()
def shut_down_obsolete_pr_sandboxes():
    """
    Shut down instances whose PRs got merged (more than) one week ago.
    """
    for instance in OpenEdXInstance.objects.filter(watchedpullrequest__isnull=False):
        pr = github.get_pr_info_by_number(
            instance.watchedpullrequest.target_fork_name,
            instance.watchedpullrequest.github_pr_number
        )
        if pr['state'] == 'closed':
            closed_at = github.parse_date(pr['closed_at'])
            now = datetime.now()
            if sufficient_time_passed(closed_at, now, 7):
                instance.shut_down()


@db_task()
def terminate_obsolete_appservers_all_instances():
    """
    Terminate obsolete app servers for all instances.
    """
    for instance in OpenEdXInstance.objects.all():
        instance.terminate_obsolete_appservers()


@db_periodic_task(crontab(day='*/1', hour='1', minute='0'))
def clean_up():
    """
    Clean up obsolete VMs.

    This task runs once per day.
    """
    shut_down_obsolete_pr_sandboxes()
    terminate_obsolete_appservers_all_instances()
