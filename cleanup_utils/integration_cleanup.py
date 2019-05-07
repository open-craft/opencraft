#!/usr/bin/env python3
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
Integration cleanup script

Cleans up all AWS, Openstack and DNS resources left behind by CircleCI
cancelled runs
"""

import argparse
from datetime import datetime, timedelta
import logging
import os
from pytz import UTC

from cleanup_utils.aws_cleanup import AwsCleanupInstance
from cleanup_utils.dns_cleanup import DnsCleanupInstance
from cleanup_utils.load_balancer_cleanup import LoadBalancerCleanup
from cleanup_utils.mysql_cleanup import MySqlCleanupInstance
from cleanup_utils.openstack_cleanup import OpenStackCleanupInstance


# Constants ###################################################################

# Default age at which things should be cleaned up, in hours
DEFAULT_AGE_LIMIT = 8
DEFAULT_CUTOFF_TIME = (
    datetime.utcnow().replace(tzinfo=UTC) - timedelta(hours=DEFAULT_AGE_LIMIT)
)


# Logging #####################################################################

logger = logging.getLogger('integration_cleanup')

file_handler = logging.FileHandler('integration_cleanup.log')
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# Functions ###################################################################


def run_integration_cleanup(dry_run=False):
    """
    Main function responsible for the cleanup
    Calls each cleanup module to be executed
    """
    logger.setLevel(logging.DEBUG)

    logger.info("Running integration cleanup tool...")
    if dry_run:
        logger.info(
            "  > Using DRY_RUN mode: no actual changes will be done to any "
            "resources."
        )

    # Clean up AWS
    aws_cleanup = AwsCleanupInstance(
        age_limit=DEFAULT_CUTOFF_TIME,
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        dry_run=dry_run
    )
    aws_cleanup.run_cleanup()

    # Clean up OpenStack provider
    openstack_settings = {
        'auth_url': os.environ['OPENSTACK_AUTH_URL'],
        'username': os.environ['OPENSTACK_USER'],
        'password': os.environ['OPENSTACK_PASSWORD'],
        'project_id': os.environ['OPENSTACK_TENANT'],
        'region_name': os.environ['OPENSTACK_REGION'],
    }
    os_cleanup = OpenStackCleanupInstance(
        age_limit=DEFAULT_CUTOFF_TIME,
        openstack_settings=openstack_settings,
        dry_run=dry_run
    )
    os_cleanup.run_cleanup()

    # Run MySQL cleanup
    mysql_cleanup = MySqlCleanupInstance(
        age_limit=DEFAULT_AGE_LIMIT,
        url=os.environ['DEFAULT_INSTANCE_MYSQL_URL'],
        domain=os.environ['DEFAULT_INSTANCE_BASE_DOMAIN'],
        drop_dbs_and_users=os.environ.get('DROP_INTEGRATION_DBS_AND_USERS', 'False').lower() == 'true',
        dry_run=dry_run
    )
    mysql_cleanup.run_cleanup()

    # Run DNS cleanup
    dns_cleanup = DnsCleanupInstance(
        zone_id=int(os.environ['GANDI_ZONE_ID']),
        api_key=os.environ['GANDI_API_KEY'],
        dry_run=dry_run
    )
    # Run DNS cleanup erasing all integration entries except for those on
    # the deletion_blacklist
    hashes_to_clean = (
        aws_cleanup.cleaned_up_hashes + os_cleanup.cleaned_up_hashes +
        mysql_cleanup.cleaned_up_hashes
    )
    dns_cleanup.run_cleanup(
        hashes_to_clean=hashes_to_clean
    )

    load_balancer_cleanup = LoadBalancerCleanup(
        load_balancer_address=os.environ['DEFAULT_LOAD_BALANCING_SERVER'].partition('@')[-1],
        fragment_prefix=os.environ.get('LOAD_BALANCER_FRAGMENT_NAME_PREFIX', 'integration-'),
        age_limit=DEFAULT_AGE_LIMIT,
        dry_run=dry_run,
    )

    load_balancer_cleanup.run_cleanup()

    logger.info("\nIntegration cleanup tool finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cleanup all unused resources from integration runs that "
                    "might have been left behind."
    )
    parser.add_argument(
        '--dry_run',
        action='store_true',
        default=False,
        help="""
            Runs this script in read only mode, not actually cleaning up the resources.
            Useful for checking if changes in the script are working correctly.
        """
    )
    args = parser.parse_args()

    run_integration_cleanup(args.dry_run)
