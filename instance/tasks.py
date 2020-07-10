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
Worker tasks for instance hosting & management
"""

# Imports #####################################################################

from datetime import datetime
import logging
from typing import Optional

from django.conf import settings
from django.db import connection
from django.db.models import F
from django.utils import timezone
from huey.api import crontab
from huey.contrib.djhuey import db_periodic_task, db_task

from instance.models.load_balancer import LoadBalancingServer
from instance.models.log_entry import LogEntry
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_deployment import OpenEdXDeployment
from instance.models.openedx_instance import OpenEdXInstance
from instance.utils import sufficient_time_passed
from pr_watch import github


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Tasks #######################################################################


@db_task()
def start_deployment(
        instance_ref_id: int,
        deployment_id: int,
        mark_active_on_success: bool = False,
        num_attempts: int = 1,
        success_tag: Optional[str] = None,
        failure_tag: Optional[str] = None,
) -> Optional[int]:
    """
    Start the deployment for an existing instance.

    :param instance_ref_id: ID of an InstanceReference (instance.ref.pk)
    :param deployment_id: ID of an OpenEdXDeployment (OpenEdXDeployment.pk)
    :param mark_active_on_success: Optionally mark the new AppServer as active when the provisioning completes.
    :param num_attempts: Optionally retry up to 'num_attempts' times.
    :param success_tag: Optionally tag the instance with 'success_tag' when the deployment succeeds.
    :param failure_tag: Optionally tag the instance with 'failure_tag' when the deployment fails.
    :return: The ID of the new deployment.
    """
    logger.info('Retrieving instance: ID=%s', instance_ref_id)
    instance = OpenEdXInstance.objects.get(ref_set__pk=instance_ref_id)

    logger.info('Retrieving deployment: ID=%s', instance_ref_id)
    deployment = OpenEdXDeployment.objects.get(pk=deployment_id)

    if deployment.cancelled:
        logger.info('Deployment %s was cancelled, returning.', deployment.id)
        return False

    logger.info('Spawning servers for deployment %s [%s]', deployment, deployment.id)
    # Launch configured number of appservers for instance
    appserver_spawn_tasks = spawn_appserver.map(
        (instance_ref_id, mark_active_on_success, False, num_attempts, success_tag, failure_tag, deployment.id)
        for _ in range(instance.openedx_appserver_count)
    )

    appserver_ids = appserver_spawn_tasks.get(blocking=True)

    if not all(appserver_ids):
        return False

    # For redundancy - if app server deployment was successful even after cancelling, we prevent the change in
    # active appserver here
    deployment = OpenEdXDeployment.objects.get(pk=deployment_id)
    if deployment.cancelled:
        logger.info('Deployment %s was cancelled, returning.', deployment.id)
        return False

    # If this deployment is to be marked active on success, others should be deactivated automatically
    if mark_active_on_success:
        other_appservers = instance.appserver_set.filter(_is_active=True).exclude(pk__in=appserver_ids)
        for appserver_to_deactivate in other_appservers:
            logger.info('Deactivating %s [%s]', appserver_to_deactivate, appserver_to_deactivate.id)
            appserver_to_deactivate.make_active(active=False)
    return deployment.pk


@db_task()
def spawn_appserver(
        instance_ref_id,
        mark_active_on_success=False,
        deactivate_old_appservers=False,
        num_attempts=1,
        success_tag=None,
        failure_tag=None,
        deployment_id=None,
):
    """
    Create a new AppServer for an existing instance.

    instance_ref_id should be the ID of an InstanceReference (instance.ref.pk)

    Optionally mark the new AppServer as active when the provisioning completes.
    Optionally deactivate old AppServers when the provisioning completes.
    Optionally retry up to 'num_attempts' times.
    Optionally tag the instance with 'success_tag' when the deployment succeeds,
    or failure_tag if it fails.
    Optionally associate the AppServer with a deployment.
    """
    logger.info('Retrieving instance: ID=%s', instance_ref_id)
    instance = OpenEdXInstance.objects.get(ref_set__pk=instance_ref_id)

    # NOTE: this is not async; blocks up to an hour.
    # The actual appserver model is created fairly quickly though (after
    # instance-wide provisioning things happen (mysql, dns records, mongo, s3,
    # rabbitmq, etc.) but before appserver provision happens)
    appserver = instance.spawn_appserver(
        num_attempts=num_attempts,
        success_tag=success_tag,
        failure_tag=failure_tag,
        deployment_id=deployment_id,
    )

    if appserver and mark_active_on_success:
        make_appserver_active(appserver, active=True, deactivate_others=deactivate_old_appservers)

    # Huey doesn't seem to resolve properly if the result of a task is so return False
    return appserver or False


@db_task()
def make_appserver_active(appserver_id, active=True, deactivate_others=False):
    """
    Mark an AppServer as active or inactive.

    :returns
        True if the appserver was made active,
        False if the corresponding server was not healthy and thus the appserver was not made active.
    """
    appserver = OpenEdXAppServer.objects.get(pk=appserver_id)
    if not appserver.server.status.is_healthy_state:
        appserver.server.update_status()
        if not appserver.server.status.is_healthy_state:
            logger.info('Not %s %s: ID=%s since the server is not Ready.', "Activating" if active else "Deactivating",
                        appserver, appserver_id)
            return False

    logger.info('%s %s: ID=%s', "Activating" if active else "Deactivating", appserver, appserver_id)
    appserver.make_active(active=active)
    if active and deactivate_others:
        other_appservers = appserver.instance.appserver_set.filter(_is_active=True).exclude(pk=appserver_id)
        for appserver_to_deactivate in other_appservers:
            logger.info('Deactivating %s [%s]', appserver_to_deactivate, appserver_to_deactivate.id)
            appserver_to_deactivate.make_active(active=False)

    return True


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
        if pr['state'] == 'closed' and not instance.ref.is_archived:
            closed_at = github.parse_date(pr['closed_at'])
            now = datetime.now()
            if sufficient_time_passed(closed_at, now, 7):
                instance.logger.info("Shutting down obsolete sandbox instance")
                instance.archive()


@db_task()
def terminate_obsolete_appservers_all_instances():
    """
    Terminate obsolete app servers for all instances.
    """
    for instance in OpenEdXInstance.objects.all():
        instance.logger.info("Terminating obsolete appservers for instance")
        instance.terminate_obsolete_appservers()


@db_periodic_task(crontab(day='*/1', hour='1', minute='0'))
def clean_up():
    """
    Clean up obsolete VMs.

    This task runs once per day.
    """
    shut_down_obsolete_pr_sandboxes()
    terminate_obsolete_appservers_all_instances()


@db_periodic_task(crontab())
def reconfigure_dirty_load_balancers():
    """
    Any load balancers that are dirty need to be reconfigured.

    This task runs every minute.
    """
    logger.info('Reconfiguring all dirty load balancers')
    for load_balancer in LoadBalancingServer.objects.filter(
            configuration_version__gt=F('deployed_configuration_version')
    ):
        load_balancer.reconfigure(mark_dirty=False)


@db_periodic_task(crontab(day='*/1', hour='0', minute='0'))
def delete_old_logs():
    """
    Delete old log entries.

    For performance reasons, we execute raw SQL against the LogEntry model's table.

    This task runs every day.
    """
    cutoff = timezone.now() - timezone.timedelta(days=settings.LOG_DELETION_DAYS)
    query = (
        "DELETE FROM {table} "
        "WHERE {table}.created < '{cutoff}'::timestamptz".format(
            table=LogEntry._meta.db_table,
            cutoff=cutoff.isoformat(),
        )
    )
    logger.info(query)
    with connection.cursor() as cursor:
        cursor.execute(query)
