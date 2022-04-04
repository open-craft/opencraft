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
from typing import Optional, List
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.core.mail import EmailMessage
from django.db import connection
from django.db.models import Q
from django.utils import timezone
from huey.api import crontab
from huey.contrib.djhuey import db_periodic_task, db_task, HUEY

from instance.models.log_entry import LogEntry
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_deployment import OpenEdXDeployment
from instance.models.openedx_instance import OpenEdXInstance
from instance.utils import sufficient_time_passed
from userprofile.models import UserProfile
from pr_watch import github


# Logging #####################################################################

logger = logging.getLogger(__name__)

# Constants  ##################################################################

KILL_ZOMBIES_CRON_SCHEDULE = settings.KILL_ZOMBIES_SCHEDULE.split()

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
        return

    logger.info('Spawning servers for deployment %s [%s]', deployment, deployment.id)
    old_server_ids = list(instance.appserver_set.filter(_is_active=True).values_list('id', flat=True))
    # Launch configured number of appservers for instance
    for _ in range(instance.openedx_appserver_count):
        # NOTE: Though this does provision multiple servers in parallel, issues have been known to occur
        # for deploying multiple instances at once in the case of outstanding migrations.
        spawn_appserver(
            instance_ref_id=instance_ref_id,
            mark_active_on_success=mark_active_on_success,
            num_attempts=num_attempts,
            success_tag=success_tag,
            failure_tag=failure_tag,
            deployment_id=deployment.id,
            old_server_ids=old_server_ids,
            target_count=instance.openedx_appserver_count,
        )


@db_task()
def check_deactivation(
        result: bool,
        instance_ref_id: int = None,
        deployment_id: int = None,
        old_server_ids: List[int] = None,
        target_count: int = None,
):
    """
    Called in pipeline with make_appserver_active when the current deployment is meant to deactivate old servers
    upon success. Since any particular server could be the last one, this checks to make sure that the correct number
    of servers which are new are now available, and that the current deployment hasn't been cancelled.

    If this is the case, it deactivates all the old app servers.
    """
    if not result:
        # This function is chained after mark_appserver_active. If that function failed, we already know things aren't
        # OK and bail out.
        logger.info('Marking appserver active failed. Returning.')
        return

    # One last chance to prevent activation from switching over, in case some other deployment is now taking precedence.
    # For redundancy - if app server deployment was successful even after cancelling, we prevent the change in
    # active appserver here
    deployment = OpenEdXDeployment.objects.get(pk=deployment_id)
    if deployment.cancelled:
        logger.info('Deployment %s was cancelled, returning.', deployment.id)
        return

    instance = OpenEdXInstance.objects.get(ref_set__pk=instance_ref_id)

    # If this deployment is to be marked active on success, others should be deactivated automatically
    current_count = instance.appserver_set.exclude(id__in=old_server_ids).filter(_is_active=True).count()
    if current_count == target_count:
        other_appservers = instance.appserver_set.filter(id__in=old_server_ids, _is_active=True)
        for appserver_to_deactivate in other_appservers:
            logger.info('Deactivating %s [%s]', appserver_to_deactivate, appserver_to_deactivate.id)
            appserver_to_deactivate.make_active(active=False)
    else:
        logger.info('Not (yet) deactivating old servers. %s/%s ready.', current_count, target_count)
    return


@db_task()
def spawn_appserver(
        instance_ref_id,
        mark_active_on_success=False,
        num_attempts=1,
        success_tag=None,
        failure_tag=None,
        deployment_id=None,
        old_server_ids=None,
        target_count=None,
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
        pipeline = make_appserver_active.s(appserver, active=True).then(
            check_deactivation,
            instance_ref_id=instance_ref_id,
            deployment_id=deployment_id,
            old_server_ids=old_server_ids,
            target_count=target_count,
        )
        HUEY.enqueue(pipeline)


@db_task()
def make_appserver_active(appserver_id, active=True):
    """
    Mark an AppServer as active or inactive.

    :returns
        True if the appserver was made active,
        False if the corresponding server was not healthy and thus the appserver was not made active.
    """
    appserver = OpenEdXAppServer.objects.get(id=appserver_id)
    if not appserver.server.status.is_healthy_state:
        appserver.server.update_status()
        if not appserver.server.status.is_healthy_state:
            logger.info('Not %s %s: ID=%s since the server is not Ready.', "Activating" if active else "Deactivating",
                        appserver, appserver_id)
            return False

    logger.info('%s %s: ID=%s', "Activating" if active else "Deactivating", appserver, appserver_id)
    appserver.make_active(active=active)
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
        instance.logger.info("Terminating obsolete appservers for instance %s", instance.domain)
        try:
            instance.terminate_obsolete_appservers()
        except Exception:  # pylint:disable=broad-except
            instance.logger.exception('Error deleting the obsolete appservers for instance %s', instance.domain)


@db_task()
def terminate_appserver(appserver_id):
    """
    Terminate a appserver on the background (in worker thread).
    """
    logger.info("Terminating appserver %s.", appserver_id)
    try:
        app_server = OpenEdXAppServer.objects.get(id=appserver_id)
        app_server.terminate_vm()
    except Exception as exc:  # pylint:disable=broad-except
        logger.exception('Error terminating appserver %s: %s', appserver_id, exc)


@db_periodic_task(crontab(day='*/1', hour='1', minute='0'))
def clean_up():
    """
    Clean up obsolete VMs.

    This task runs once per day.
    """
    shut_down_obsolete_pr_sandboxes()
    terminate_obsolete_appservers_all_instances()


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


if settings.CLEANUP_OLD_BETATEST_USERS:

    @db_periodic_task(crontab(day='3', hour='0', minute='0'))
    def cleanup_old_betatest_users():
        """
        Delete old betatest users.

        Finds users that meet following conditions -
            - Associated with a betatest application
            - Not a staff or superuser
            - Associated instance doesn't exists or already deleted
            - Betatest application created at least ``INACTIVE_USER_DAYS`` days ago
            - Last logged in at least ``INACTIVE_USER_DAYS`` days ago

        If those users are still active, marks as inactive. Updated ``UserProfile.modified``
        to track when marked as inactive.

        If those users are inactive for at least ``DELETE_USER_DAYS`` days, deletes them.

        So this actually deletes an active old user after ``INACTIVE_USER_DAYS + DELETE_USER_DAYS`` days.

        This job runs Wednesday, every week.
        """

        inactive_cutoff = timezone.now() - timezone.timedelta(
            days=settings.INACTIVE_OLD_BETATEST_USER_DAYS
        )

        delete_cutoff = timezone.now() - timezone.timedelta(
            days=settings.DELETE_OLD_BETATEST_USER_DAYS
        )

        queryset = get_user_model().objects.filter(
            # has a beta test application
            betatestapplication__isnull=False,

            # are not staff or superuser
            is_staff=False,
            is_superuser=False,

            # don't belong to any organization (ex. opencraft)
            profile__organization=None,

            # instances doesn't exists or already deleted
            profile__instancereference__isnull=True,
            openedxinstance__isnull=True,
            openedxappserver__isnull=True,

            # at least specified days old
            betatestapplication__created__lte=inactive_cutoff
        ).filter(
            # never logged in or logged in ``inactive_cutoff`` days ago
            Q(last_login=None) | Q(last_login__lte=inactive_cutoff)
        )

        # mark user as inactive. Update ``Profile.modified`` to current time.
        users_to_inactive = queryset.filter(is_active=True)
        logger.info('Marking %s users as inactive.', users_to_inactive.count())
        users_to_inactive.update(is_active=False)
        UserProfile.objects.filter(user__in=users_to_inactive).update(modified=timezone.now())

        # deletes inactive users that last modified ``DELETE_USER_DAYS`` ago.
        users_to_delete = queryset.filter(is_active=False, profile__modified__lte=delete_cutoff)
        logger.info('Deleting %s users.', users_to_delete.count())
        users_to_delete.delete()


class KillZombiesRunner:
    """
    Helper class to run `kill_zombies_periodically`
    """

    def __init__(self):
        self.region: str = settings.OPENSTACK_REGION
        self.recipient: list = [email for _, email in settings.ADMINS]
        self.threshold: int = settings.KILL_ZOMBIES_WARNING_THRESHOLD

    def send_email(self, subject: str, body: str) -> int:
        """
        Utility method for sending emails
        """
        if self.recipient:
            email = EmailMessage(
                subject, body, settings.DEFAULT_FROM_EMAIL, self.recipient
            )
            email.send()
        else:
            logging.info("Email recipient is undefined. Skipping email.")

    def trigger_warning(self, num_zombies):
        """
        Warns when more than `threshold` VMs will be terminated
        """
        subject = "Zombie instances are over the current threshold ({})".format(
            self.threshold
        )
        body = (
            "The number of zombie OpenStack VMs ({}) in the {} region "
            "is over the KILL_ZOMBIES_WARNING_THRESHOLD ({}).\n"
            "These instances will be terminated using the `kill_zombies` command."
        ).format(num_zombies, self.region, self.threshold)
        logging.info(
            "%s\nSending an email notification to: %s",
            body, self.recipient
        )
        self.send_email(subject, body)

    def get_zombie_servers_count(self, stdout: str) -> int:
        """
        If there are servers to terminate, a `kill_zombies` dry run will warn:
        "Would have terminated {} zombies" to stdout.
        """
        num_instances = 0
        if "No servers found in region" in stdout:
            return num_instances
        try:
            num_instances = int(stdout.split("Would have terminated")[1].split()[0])
        except (IndexError, ValueError):
            logger.info("Received unexpected input from dry run. Defaulting to zero")
        return num_instances

    def run(self):
        """
        Main method for running the task
        """
        try:
            dry_run_output, output = "", ""
            dry_run_output = call_command(
                "kill_zombies",
                region=self.region,
                dry_run=True,
            )
            num_of_zombies = self.get_zombie_servers_count(dry_run_output)
            if num_of_zombies > self.threshold:
                self.trigger_warning(num_of_zombies)
            if num_of_zombies != 0:
                output = call_command("kill_zombies", region=self.region)
                logging.info(
                    "Task `kill_zombies_periodically` ran successfully "
                    "and terminated %s zombies", num_of_zombies
                )
            else:
                logging.info(
                    "Found zero zombies to terminate. "
                    "Task `kill_zombies_periodically` ran successfully."
                )
        except CommandError:
            logger.error(
                "Task `kill_zombies` command failed. Sending notification email"
            )
            subject = "Terminate zombie instances command failed"
            body = (
                "Scheduled execution of `kill_zombies` command failed. "
                "Log entries are displayed below:"
                "%s\n%s"
            ) % (dry_run_output, output)
            self.send_email(subject, body)
            return False
        return True


if settings.KILL_ZOMBIES_ENABLED:
    @db_periodic_task(crontab(
        minute=KILL_ZOMBIES_CRON_SCHEDULE[0],
        hour=KILL_ZOMBIES_CRON_SCHEDULE[1],
        day=KILL_ZOMBIES_CRON_SCHEDULE[2],
        month=KILL_ZOMBIES_CRON_SCHEDULE[3],
        day_of_week=KILL_ZOMBIES_CRON_SCHEDULE[4],
    ))
    def kill_zombies_task():
        """
        A wrapper for `kill_zombies_periodically` so it only
        exists when KILL_ZOMBIES_ENABLED is true
        """
        task_runner = KillZombiesRunner()
        logging.info("Executing periodic task `kill_zombies_periodically`")
        task_runner.run()
