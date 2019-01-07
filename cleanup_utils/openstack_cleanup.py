# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
OpenStack Cleanup Script

Cleans up all OpenStack VM's left behind by the CI
"""

from datetime import datetime
import logging
from novaclient import client
import pytz

# Logging #####################################################################

logger = logging.getLogger('integration_cleanup')


# Classes #####################################################################

class OpenStackCleanupInstance:
    """
    Handles the search and cleanup of all unused OpenStack resources used
    by CircleCI
    """
    def __init__(self, age_limit, openstack_settings, dry_run=False):
        """
        Set's up Nova client
        """
        self.dry_run = dry_run
        self.age_limit = age_limit
        self.cleaned_up_hashes = []

        self.nova = client.Client(
            "2.0",
            auth_url=openstack_settings['auth_url'],
            username=openstack_settings['username'],
            password=openstack_settings['password'],
            project_id=openstack_settings['project_id'],
            region_name=openstack_settings['region_name']
        )

    def get_active_circle_ci_instances(self):
        """
        Returns list of active instances running on the OpenStack provider
        that have been created by CircleCI

        Note: key_name parameter is useless if ran with a user that is not an
              admin. It's good to check twice somewhere else.
        """
        server_list = self.nova.servers.list(
            search_opts={
                'key_name': 'circleci'
            }
        )
        # Filter any keys that are not from circleci in case our query
        # was ignored
        server_list = [s for s in server_list if s.key_name == 'circleci']
        return server_list

    def run_cleanup(self):
        """
        Runs the cleanup of OpenStack provider
        """
        logger.info("\n --- Starting OpenStack Provider Cleanup ---")
        if self.dry_run:
            logger.info("Running in DRY_RUN mode, no actions will be taken.")

        ci_instances = self.get_active_circle_ci_instances()
        logger.info("Found %s active instances using CircleCI keys...", len(ci_instances))

        for instance in ci_instances:
            logger.info("  > Checking instance %s...", instance.name)
            logger.info(
                "    * id=%s, key_name=%s, created=%s",
                instance.id,
                instance.key_name,
                instance.created
            )
            # Double-check to make sure that the instance is using the circleci keypair.
            if instance.key_name != 'circleci':
                logger.info(
                    "    * SKIPPING: Instance keypair name %s != 'circleci'!",
                    instance.key_name
                )
                continue

            # Check if it's a valid date and add UTC timezone
            try:
                instance_age_unaware = datetime.strptime(
                    instance.created,
                    '%Y-%m-%dT%H:%M:%SZ'
                )
                instance_age = instance_age_unaware.replace(tzinfo=pytz.UTC)
            except ValueError:
                logger.warning(
                    "    * WARNING: Coudn't parse instance age (%s)! This instance will be skipped.",
                    instance.created
                )
                instance_age = None

            # If instance is older than age limit
            if instance_age and instance_age < self.age_limit:
                # Get instance name in format edxapp-HASHinteg-1
                self.cleaned_up_hashes.append(
                    instance.name.split('-')[1][:-5]
                )

                # Terminate the servers
                logger.info(
                    "    * TERMINATING instance (created at: %s, termination threshold: %s)...",
                    instance_age,
                    self.age_limit
                )
                if not self.dry_run:
                    try:
                        instance.delete()
                    except Exception as e: # pylint: disable=broad-except
                        logger.warning(
                            "    * WARNING: Unable to delete instance. Error: %s.",
                            e,
                        )

            else:
                logger.info(
                    "    * SKIPPING: Instance was created at %s but the cut-off age threshold is %s.",
                    instance_age,
                    self.age_limit
                )
