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
Instance - reprovision_buckets unit tests
"""
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO
from testfixtures import LogCapture

from instance.models.openedx_instance import OpenEdXInstance


class ReprovisionBucketsTestCase(TestCase):
    """
    Test cases for the `reprovision_buckets` management command.
    """

    def test_no_instances(self):
        """
        Verify that the command correctly notifies the user that there are no instances for migration.
        """
        with LogCapture() as captured_logs:
            call_command(
                'reprovision_buckets',
                stdout=StringIO(),
            )
        # Verify the logs
        self.assertIn(
            'Found "0" active instances',
            [l[2] for l in captured_logs.actual()])

    @patch(
        'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._enable_bucket_versioning')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_bucket_lifecycle')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_bucket_cors')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._perform_create_bucket')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._is_bucket_exists')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin._update_iam_policy')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.create_iam_user')
    def test_migrate(self,
                     mock_create_iam_user,
                     mock_update_iam,
                     mock_check_if_bucket_exists,
                     mock_create_bucket,
                     mock_update_cors,
                     mock_update_lifecycle,
                     mock_enable_versioning,
                     mock_consul):
        """
        Verify that the command correctly reprovision the bucket for an instance.
        """
        OpenEdXInstance.objects.create(
            sub_domain='test', name='test instance', storage_type=OpenEdXInstance.S3_STORAGE)
        with LogCapture() as captured_logs:
            call_command(
                'reprovision_buckets',
                stdout=StringIO(),
            )
            # Verify the logs
        self.assertIn(
            'Found "1" active instances',
            set(l[2] for l in captured_logs.actual()))

        mock_update_iam.assert_called_once_with()
        mock_update_cors.assert_called_once_with()
        mock_update_lifecycle.assert_called_once_with()
        mock_enable_versioning.assert_called_once_with()
