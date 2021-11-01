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
This management command will deprovision the S3 bucket for archived instances.
"""

from datetime import timedelta
import logging

from django.core.management.base import BaseCommand
from django.utils import timezone

from instance.models.openedx_instance import OpenEdXInstance

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This management command will deprovision the S3 buckets of instance which
    have been archived longer than 3 months ago.

    It accepts a list of instance ref ids in case buckets of non-sandbox
    instances should get archived.
    """
    help = (
        'Deprovision S3 buckets for archived instances'
    )

    @staticmethod
    def _check_positive_int(arg):
        """
        Ensure that num-days-archived is a positive (integer) number
        """
        arg = int(arg)
        if arg < 0:
            raise ValueError("the value of num_days_archived must be greater or equal to zero")

    def add_arguments(self, parser):
        parser.add_argument(
            '--instance-ref-ids',
            nargs='*',
            type=self._check_positive_int,
            help='list of instance ref ids to deprovision for'
        )
        parser.add_argument(
            '--num-days-archived',
            nargs='?',
            type=int,
            default=3,
            help='ensure at least num_days_archived since instance has been archived'
        )

    def handle(self, *args, **options):
        """
        Deprovisions the S3 bucket for the instance provided by
        instance_ref_ids or if instance_ref_ids is not given for all sandbox
        instances.
        """

        instance_ref_ids = options['instance_ref_ids']
        num_days_archived = options['num_days_archived']

        # Identify instances that can be deprovisioned
        if not instance_ref_ids:
            # if instance_ref_ids are not specified we will archive sandbox instances
            archived_instances = OpenEdXInstance.objects.filter(
                ref_set__is_archived=True,
                internal_lms_domain__contains=".sandbox.",
                s3_bucket_name__isnull=False
            )
        else:
            archived_instances = OpenEdXInstance.objects.filter(
                ref_set__is_archived=True,
                s3_bucket_name__isnull=False,
                ref_set__id__in=instance_ref_ids
            )
        archived_instances = [
            i for i in archived_instances if
            i.latest_archiving_date
            and i.latest_archiving_date + timedelta(days=num_days_archived) < timezone.now()
        ]
        LOG.info('Found "%d" instances for which S3 buckets can be deprovisioned', len(archived_instances))
        for instance in archived_instances:
            LOG.info('Triggering deprovision_s3 from management command for instance id %d', instance.id)
            instance.deprovision_s3()
