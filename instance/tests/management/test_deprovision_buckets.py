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
Instance - deprovision_buckets unit tests
"""
import re
from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from django.utils.six import StringIO
from testfixtures import LogCapture

from instance.gandi import GandiV5API

from instance.models.openedx_instance import OpenEdXInstance


class DeprovisionBucketsTestCase(TestCase):
    """
    Test cases for the `reprovision_buckets` management command.
    """

    def test_no_instances(self):
        """
        Verify that the command correctly notifies the user that there are no instances for migration.
        """
        with LogCapture() as captured_logs:
            call_command(
                'deprovision_buckets',
                stdout=StringIO(),
            )
        # Verify the logs
        self.assertIn(
            'Found "0" instances for which S3 buckets can be deprovisioned',
            [l[2] for l in captured_logs.actual()])

    @patch(
        'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._enable_bucket_versioning')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_bucket_lifecycle')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_bucket_cors')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._perform_create_bucket')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_iam_policy')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.create_iam_user')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._get_bucket_objects')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._delete_s3_bucket')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._delete_s3_user_policy')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._delete_s3_user')
    @patch.object(GandiV5API, 'remove_dns_record')
    @patch('instance.models.openedx_instance.OpenEdXInstance.clean_up_appserver_dns_records')
    @patch('instance.tests.models.factories.openedx_instance.OpenEdXInstance.purge_consul_metadata')
    @patch('instance.tests.models.factories.openedx_instance.OpenEdXInstance.deprovision_rabbitmq')
    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    @patch('instance.models.mixins.ansible.AnsibleAppServerMixin._run_playbook', return_value=("", 0))
    def test_deprovision_s3_of_archived_sandbox(self, *mocks):
        """
        Verify that the command correctly deprovisions the bucket for an archived sandbox instance.
        """
        instance = OpenEdXInstance.objects.create(
            sub_domain='test',
            name='test instance',
            storage_type=OpenEdXInstance.S3_STORAGE,
            s3_bucket_name='testbucket',
            internal_lms_domain='.sandbox.'
        )
        instance.archive()
        # instances need to be archived for at least 3 months for us to be able to deprovision the s3 buckets
        with LogCapture() as captured_logs:
            call_command(
                'deprovision_buckets',
                stdout=StringIO(),
            )
        # Verify the logs
        self.assertIn(
            'Found "0" instances for which S3 buckets can be deprovisioned',
            set(l[2] for l in captured_logs.actual()))

        # let's pretend the instance was archived 90 days and 1 minute ago
        for log_entry in instance.log_entries:
            if re.search(r'Archiving instance finished.', log_entry.text):
                log_entry.created = log_entry.created - timedelta(days=90, minutes=1)
                log_entry.save()
        with LogCapture() as captured_logs:
            call_command(
                'deprovision_buckets',
                stdout=StringIO(),
            )

        self.assertIn(
            'Found "1" instances for which S3 buckets can be deprovisioned',
            set(l[2] for l in captured_logs.actual()))

        self.assertTrue(
            any(re.search(r'Deprovisioning S3 finished.', l[2]) for l in captured_logs.actual()))

    @patch(
        'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._enable_bucket_versioning')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_bucket_lifecycle')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_bucket_cors')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._perform_create_bucket')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_iam_policy')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.create_iam_user')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._get_bucket_objects')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._delete_s3_bucket')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._delete_s3_user_policy')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._delete_s3_user')
    @patch.object(GandiV5API, 'remove_dns_record')
    @patch('instance.models.openedx_instance.OpenEdXInstance.clean_up_appserver_dns_records')
    @patch('instance.tests.models.factories.openedx_instance.OpenEdXInstance.purge_consul_metadata')
    @patch('instance.tests.models.factories.openedx_instance.OpenEdXInstance.deprovision_rabbitmq')
    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    @patch('instance.models.mixins.ansible.AnsibleAppServerMixin._run_playbook', return_value=("", 0))
    def test_deprovision_s3_of_archived_client_instance(self, *mocks):
        """
        Verify that the command correctly deprovisions the bucket for an archived client instance.
        """
        instance = OpenEdXInstance.objects.create(
            sub_domain='test',
            name='test instance',
            storage_type=OpenEdXInstance.S3_STORAGE,
            s3_bucket_name='testbucket'
        )
        instance.archive()

        # instances need to be archived for at least 3 months for us to be able to deprovision the s3 buckets
        with LogCapture() as captured_logs:
            call_command(
                'deprovision_buckets',
                instance_ref_ids=[instance.ref.id],
                stdout=StringIO(),
            )
        # Verify the logs
        self.assertIn(
            'Found "0" instances for which S3 buckets can be deprovisioned',
            set(l[2] for l in captured_logs.actual()))

        # let's pretend the instance was archived 90 days and 1 minute ago
        for log_entry in instance.log_entries:
            if re.search(r'Archiving instance finished.', log_entry.text):
                log_entry.created = log_entry.created - timedelta(days=90, minutes=1)
                log_entry.save()
        with LogCapture() as captured_logs:
            call_command(
                'deprovision_buckets',
                instance_ref_ids=[instance.ref.id],
                stdout=StringIO(),
            )

        self.assertIn(
            'Found "1" instances for which S3 buckets can be deprovisioned',
            set(l[2] for l in captured_logs.actual()))

        self.assertTrue(
            any(re.search(r'Deprovisioning S3 finished.', l[2]) for l in captured_logs.actual()))
