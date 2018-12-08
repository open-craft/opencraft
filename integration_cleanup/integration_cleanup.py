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
import os
from pytz import UTC

from aws_cleanup import AwsCleanupInstance
from openstack_cleanup import OpenStackCleanupInstance
from dns_cleanup import DnsCleanupInstance


default_age_limit = datetime.utcnow().replace(tzinfo=UTC) - timedelta(days=3)
default_policy_name = 'allow_access_s3_bucket'

def main():
    """
    Main function responsible for the cleanup
    """
    parser = argparse.ArgumentParser(
        description="Cleanup all unused resources from integration runs that "
                    "have been cancelled or failed."
    )
    parser.add_argument(
        '--dry_run',
        action='store_true',
        help='sum the integers (default: find the max)'
    )

    # Clean up AWS
    aws_cleanup = AwsCleanupInstance(
        age_limit=default_age_limit,
        policy_name=default_policy_name,
        aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'],
        dry_run=True
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
        age_limit=default_age_limit,
        openstack_settings=openstack_settings,
        dry_run=True
    )
    os_cleanup.run_cleanup()

    # Run DNS cleanup
    dns_cleanup = DnsCleanupInstance(
        zone_id=int(os.environ['GANDI_ZONE_ID']),
        api_key=os.environ['GANDI_API_KEY'],
        dry_run=True
    )
    # Run DNS cleanup erasing only DNS entries related to the cleaned VM's
    dns_cleanup.run_cleanup(os_cleanup.cleaned_ips)


if __name__ == "__main__":
    main()
