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
Instance app - Instance Redeployment management command
"""

# Imports #####################################################################

import time
import logging
import yaml

from django.core.management.base import BaseCommand

from instance.models.appserver import Status as AppserverStatus
from instance.models.instance import InstanceTag
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.load_balancer import LoadBalancingServer
from instance.tasks import spawn_appserver

# Helpers #####################################################################


LOG = logging.getLogger(__name__)


def load_yaml(string):
    """
    Return the dict parsed from the given yaml string.

    If the string begins with @, then read from the file there named.
    """
    if string.startswith('@'):
        content = open(string[1:])
    else:
        content = string
    return yaml.load(content)


# Classes #####################################################################


class Command(BaseCommand):
    """
    instance_redeploy management command class
    """
    help = (
        'Redeploys a given set of instances by updating their configuration, spawning new new appservers, and'
        ' activating them when successful.'
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.options = {}
        self.retried = {}

    def add_arguments(self, parser):
        """
        Add named arguments.
        """
        parser.add_argument(
            '--tag',
            type=str,
            required=True,
            help='Base name of the tag used to mark instances for redeployment.  After the redeployment is complete,'
                 'all instances which are successfully redeployed will be marked with this tag.  Instances which failed'
                 'to redeploy will be marked with tag + "-failed".  E.g., zebrawood-redeployment'
        )
        parser.add_argument(
            '--filter',
            type=load_yaml,
            default='{}',
            help='YAML containing the OpenEdXInstance queryset filter to use to select the instances to redeploy.'
                 ' Pass @path/to/file.yml to read filters from a file. '
                 ' Note that archived instances are automatically excluded. Omit to re-spawn all un-archived instances.'
        )
        parser.add_argument(
            '--update',
            type=load_yaml,
            default='{}',
            help='YAML containing the OpenEdXInstance fields and values to be updated prior to re-spawning.'
                 ' Pass @path/to/file.yml to read from a file. '
                 ' Omit to leave the instance unchanged.'
        )
        parser.add_argument(
            '--preupgrade-sql-commands',
            type=load_yaml,
            default='[]',
            help='YAML containing a list of SQL commands to execute on each instance\'s edxapp database prior '
                 'to respawning. Pass @path/to/file.yml to read from a file. Omit to skip any SQL commands.'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Pass --force to start redeployment without confirming first.'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=2,
            help='Number of appservers to spawn at once.  Ensure that you have sufficient Huey workers to support this'
                 ' many appservers, otherwise the appservers may fail to spawn.'
        )
        parser.add_argument(
            '--batch-frequency',
            type=int,
            default=10 * 60,  # 10 min default
            help='Number of seconds to wait before checking the appserver status, and (potentially) spawning the next'
                 ' batch of appservers.'
        )
        parser.add_argument(
            '--num-attempts',
            type=int,
            default=1,
            help='Number of times to try spawning an appserver for a given instance before calling it a failure.'
        )

    def handle(self, *args, **options):
        """
        Verify redeployment arguments with user, and then start redeployment loop.
        """
        self.options = options

        # Log the status report, and some more information about the given options
        self._redeployment_complete()
        LOG.info("Batch size: %d", self.options['batch_size'])
        LOG.info("Batch frequency: %s", self._format_batch_frequency())
        LOG.info("Number of upgrade attempts per instance: %d", self.options['num_attempts'])

        # Confirm redeployment
        if self._confirm_redeploy():
            LOG.info("** Starting redeployment **")
            self._do_redeployment()
            LOG.info("** Redeployment done **")
        else:
            LOG.info("** Redeployment canceled **")

    def _format_batch_frequency(self):
        """
        Return the parsed batch frequency as a user-friendly string.
        """
        frequency = self.options['batch_frequency']
        minutes, seconds = divmod(frequency, 60)
        hours, minutes = divmod(minutes, 60)
        return "{:d}:{:02d}:{:02d}".format(hours, minutes, seconds)

    @property
    def complete_tag(self):
        """
        Tag used to mark the successfully redeployed and activated instances.
        """
        return self._get_tag()

    @property
    def ongoing_tag(self):
        """
        Tag marking those instances whose redeployment is in progress.
        """
        return self._get_tag("ongoing")

    @property
    def success_tag(self):
        """
        Tag marking those instances whose redeployment succeeded, and are awaiting activation.
        """
        return self._get_tag("success")

    @property
    def failure_tag(self):
        """
        Tag marking those instances whose redeployment failed.
        """
        return self._get_tag("failure")

    def _get_tag(self, suffix=None):
        """
        Creates or returns a tag named self.options['tag'] + '-' + suffix
        """
        name = self.options['tag']
        if suffix:
            name += '-' + suffix
        tag, _ = InstanceTag.objects.get_or_create(name=name)
        return tag

    def _pending_instances(self):
        """
        Return a queryset containing the instances that need to be redeployed.

        These will match the options['filter'] (if given), and are not already tagged.
        """
        instance_filter = self.options.get('filter', {})
        instances = OpenEdXInstance.objects.filter(**instance_filter)

        # Exclude archived instances
        instances = instances.exclude(ref_set__is_archived=True)

        # Exclude any previously-tagged instances
        instances = instances.exclude(tags__in=[
            self.complete_tag,
            self.ongoing_tag,
            self.success_tag,
            self.failure_tag,
        ])

        return instances

    def _failed_instances(self):
        """
        Return a queryset containing the failed tagged instances.
        """
        return self.failure_tag.openedxinstance_set.iterator()

    def _confirm_redeploy(self):
        """
        Determine how many instances will be redeployed, and other basic stats.

        Confirm with the user that redeployment is desired (unless options['force']).
        """
        if self.options['force']:
            answer = 'yes'
        else:
            self.stdout.write("Do you want to continue? [yes/No]")
            answer = input()

        return answer.lower().startswith('y')

    def _redeployment_complete(self):
        """
        Returns True if redeployment is complete, False if it is still in progress.

        The redeployment is still in progress if there are pending or in progress instances remaining.

        Also logs a redeployment status report from the counts taken.
        """
        num_pending = self._pending_instances().count()
        num_ongoing = self.ongoing_tag.openedxinstance_set.count()
        num_failure = self.failure_tag.openedxinstance_set.count()
        num_success = self.success_tag.openedxinstance_set.count()
        num_complete = self.complete_tag.openedxinstance_set.count()

        LOG.info("******* Status *******")
        LOG.info("Instances pending redeployment: %d", num_pending)
        LOG.info("Redeployments in progress: %d", num_ongoing)
        LOG.info("Failed to redeploy: %d", num_failure)
        LOG.info("Successfully redeployed (to be activated): %d", num_success)
        LOG.info("Successfully redeployed (done): %d", num_complete)

        return num_pending == 0 and num_ongoing == 0 and num_success == 0

    def _do_mysql_commands(self, instance):
        """
        Run the MySQL commands specified by the command parameters.
        """
        mysql_commands = self.options.get('preupgrade_sql_commands', [])
        if mysql_commands:
            LOG.info("Performing MySQL commands: %s %s (%s)", instance, instance.domain, instance.id)
            cursor = instance.get_mysql_cursor_for_db('edxapp')
            if cursor is not None:
                for command in mysql_commands:
                    cursor.execute(command)
                cursor.close()

    def _do_redeployment(self):
        """
        Run the redeployment in batches, logging the status for each loop.
        """
        num_attempts = self.options['num_attempts']
        batch_size = self.options['batch_size']
        update = self.options.get('update', {})
        sleep_seconds = self.options['batch_frequency']

        # Loop termination is handled at the end of the loop
        while True:

            # 1. Activate successful instances
            reconfigure_load_balancer = False
            for instance in self.success_tag.openedxinstance_set.iterator():
                LOG.info("SUCCESS: %s [%s]", instance, instance.id)
                instance.tags.remove(self.ongoing_tag)
                instance.tags.remove(self.success_tag)

                # Make sure that the latest appserver is running
                latest_appserver = instance.appserver_set.latest('created')
                if latest_appserver.status == AppserverStatus.Running:
                    reconfigure_load_balancer = True

                    # Deactivate currently active servers
                    for appserver in instance.appserver_set.filter(_is_active=True):
                        LOG.info(' - Deactivating %s [%s]', appserver, appserver.id)
                        appserver.is_active = False
                        appserver.save()

                    # Activate the latest server
                    LOG.info(' - Activating %s [%s]', latest_appserver, latest_appserver.id)
                    latest_appserver.is_active = True
                    latest_appserver.save()

                    # Tag as complete
                    instance.tags.add(self.complete_tag)
                else:
                    # Tag as failure
                    LOG.info('FAILED: latest %s [%s] for %s is not running. (This should not happen.)',
                             latest_appserver, latest_appserver.id, instance)
                    instance.tags.add(self.failure_tag)

            # 2. Reconfigure the load balancer only once to register all new active appservers.
            #    Note: We do this here instead of passing spawn_appserver(mark_active_on_success=True),
            #    to reduce the number of times the load balancer has to be reconfigured.
            if reconfigure_load_balancer:
                lb = LoadBalancingServer.objects.get(accepts_new_backends=True)
                lb.reconfigure()

            # 3. Log failed instances
            for instance in self.failure_tag.openedxinstance_set.iterator():
                instance.tags.remove(self.ongoing_tag)
                LOG.info("FAILED: %s [%s]", instance, instance.id)

            # 4. Spawn the next batch of instances, if there's room.
            next_batch_size = batch_size - self.ongoing_tag.openedxinstance_set.count()
            for instance in self._pending_instances()[0:next_batch_size]:

                self._do_mysql_commands(instance)

                LOG.info("SPAWNING: %s [%s]", instance, instance.id)

                # Tag the instance as in progress/ongoing
                instance.tags.add(self.ongoing_tag)

                # Update any fields that need to change
                for field, value in update.items():
                    setattr(instance, field, value)
                instance.save()

                spawn_appserver(instance.ref.pk,
                                success_tag=self.success_tag,
                                failure_tag=self.failure_tag,
                                num_attempts=num_attempts)

            # 5. Stop loop if redeployment is complete.
            if self._redeployment_complete():
                break

            # Otherwise, sleep for the configured time, and loop again.
            LOG.info("Sleeping for %s", self._format_batch_frequency())
            time.sleep(sleep_seconds)
