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
This management command will reprovision the S3 bucket for each available
instance to have its configuration updated on AWS.
"""

import logging

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand

from instance.models.instance import InstanceReference

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This management command will reprovision the S3 bucket for each available
    instance to have its configuration updated on AWS.
    """
    help = (
        'Reprovision S3 buckets for all available instances'
    )

    def handle(self, *args, **options):
        """
        Reprovisions the S3 bucket for each available instance to have its
        configuration updated on AWS.
        """

        # Identify instances that need updating
        refs = InstanceReference.objects.filter(is_archived=False)
        LOG.info('Found "%d" active instances', len(refs))

        for ref in refs:
            LOG.info('Reprovisioning %s S3 bucket to update bucket and iam configuration', ref.instance.name)

            # Reprovisioning will update the necessary configuration
            try:
                ref.instance.provision_s3()
            except ClientError as e:
                LOG.error(
                    'Failed to reprovision bucket for "%s" due to: %s',
                    ref.instance.name,
                    e
                )
            else:
                LOG.info('Reprovisioned bucket for %s', ref.instance.name)
