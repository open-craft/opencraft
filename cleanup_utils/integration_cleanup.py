#!/usr/bin/env python3
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
from cleanup_utils.openstack_cleanup import OpenStackCleanupInstance
from cleanup_utils.dns_cleanup import DnsCleanupInstance


# Constants ###################################################################

DEFAULT_AGE_LIMIT = datetime.utcnow().replace(tzinfo=UTC) - timedelta(days=3)


# Logging #####################################################################

logger = logging.getLogger('integration_cleanup')

file_handler = logging.FileHandler('integration_cleanup.log')
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


# Classes #####################################################################


def main():
    """
    Main function responsible for the cleanup
    """
    parser = argparse.ArgumentParser(
        description="Cleanup all unused resources from integration runs that "
                    "might have been left behind."
    )
    parser.add_argument(
        '--dry_run',
        action='store_true',
        default=False,
        help='sum the integers (default: find the max)'
    )
    args = parser.parse_args()
    logger.setLevel(logging.DEBUG)

    logger.info("Running integration cleanup tool...")
    if args.dry_run:
        logger.info(
            "  > Using DRY_RUN mode: no actual changes will be done to any "
            "resources."
        )

    # Clean up AWS
    aws_cleanup = AwsCleanupInstance(
        age_limit=DEFAULT_AGE_LIMIT,
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        dry_run=args.dry_run
    )
    aws_cleanup.run_cleanup()

    # Clean up OpenStack provider
    openstack_settings = {
        'auth_url': os.environ['OPENSTACK_AUTH_URL'],
        'username': os.environ['OPENSTACK_USER'],
        'api_key': os.environ['OPENSTACK_PASSWORD'],
        'project_id': os.environ['OPENSTACK_TENANT'],
        'region_name': os.environ['OPENSTACK_REGION'],
    }
    os_cleanup = OpenStackCleanupInstance(
        age_limit=DEFAULT_AGE_LIMIT,
        openstack_settings=openstack_settings,
        dry_run=args.dry_run
    )
    os_cleanup.run_cleanup()

    # Run DNS cleanup
    dns_cleanup = DnsCleanupInstance(
        zone_id=int(os.environ['GANDI_ZONE_ID']),
        api_key=os.environ['GANDI_API_KEY'],
        dry_run=args.dry_run
    )
    # Run DNS cleanup erasing all integration entries except for those on
    # the deletion_blacklist
    hashes_to_clean = aws_cleanup.cleaned_up_hashes + os_cleanup.cleaned_up_hashes
    dns_cleanup.run_cleanup(
        hashes_to_clean=hashes_to_clean
    )

    logger.info("\nIntegration cleanup tool finished.")


if __name__ == "__main__":
    main()
