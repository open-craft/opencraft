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
OpenEdXInstance Storage Mixins - Tests
"""

# Imports #####################################################################

from unittest.mock import call, patch

import boto3
import ddt
import yaml
from botocore.exceptions import ClientError
from botocore.session import get_session
from botocore.stub import Stubber
from django.conf import settings
from django.test.utils import override_settings

from instance.models.mixins import storage
from instance.models.mixins.storage import StorageContainer, S3_CORS
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.utils import S3Stubber, IAMStubber


# Clients #####################################################################
iam_client = get_session().create_client('iam')
s3_client = get_session().create_client('s3')

# Tests #######################################################################


class OpenEdXStorageMixinTestCase(TestCase):
    """
    Tests for OpenEdXStorageMixin
    """

    def check_s3_vars(self, yaml_vars_string):
        """
        Check the the given yaml string includes the expected Open edX S3-related vars/values
        """
        parsed_vars = yaml.load(yaml_vars_string, Loader=yaml.SafeLoader)
        self.assertEqual(parsed_vars['AWS_ACCESS_KEY_ID'], 'test-s3-access-key')
        self.assertEqual(parsed_vars['AWS_SECRET_ACCESS_KEY'], 'test-s3-secret-access-key')

        self.assertEqual(parsed_vars['EDXAPP_AUTH_EXTRA'], {'AWS_STORAGE_BUCKET_NAME': 'test-s3-bucket-name'})
        self.assertEqual(parsed_vars['EDXAPP_AWS_ACCESS_KEY_ID'], 'test-s3-access-key')
        self.assertEqual(parsed_vars['EDXAPP_AWS_SECRET_ACCESS_KEY'], 'test-s3-secret-access-key')

        self.assertEqual(parsed_vars['XQUEUE_AWS_ACCESS_KEY_ID'], 'test-s3-access-key')
        self.assertEqual(parsed_vars['XQUEUE_AWS_SECRET_ACCESS_KEY'], 'test-s3-secret-access-key')
        self.assertEqual(parsed_vars['XQUEUE_UPLOAD_BUCKET'], 'test-s3-bucket-name')

        self.assertEqual(parsed_vars['COMMON_OBJECT_STORE_LOG_SYNC'], True)
        self.assertEqual(parsed_vars['COMMON_OBJECT_STORE_LOG_SYNC_BUCKET'], 'test-s3-bucket-name')
        self.assertEqual(parsed_vars['AWS_S3_LOGS_ACCESS_KEY_ID'], 'test-s3-access-key')
        self.assertEqual(parsed_vars['AWS_S3_LOGS_SECRET_KEY'], 'test-s3-secret-access-key')

        # Profile image backend
        self.assertEqual(parsed_vars['EDXAPP_PROFILE_IMAGE_BACKEND']['class'], 'storages.backends.s3boto.S3BotoStorage')

        opts = parsed_vars['EDXAPP_PROFILE_IMAGE_BACKEND']['options']
        self.assertEqual(opts['headers'], {'Cache-Control': 'max-age-{{ EDXAPP_PROFILE_IMAGE_MAX_AGE }}'})
        self.assertRegex(opts['location'], r'instance[\w]+_test_example_com/profile-images')

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_ansible_s3_settings(self, mock_consul):
        """
        Test that get_storage_settings() includes S3 vars, and that they get passed on to the
        AppServer
        """
        instance = OpenEdXInstanceFactory(
            storage_type='s3',
            s3_access_key='test-s3-access-key',
            s3_secret_access_key='test-s3-secret-access-key',
            s3_bucket_name='test-s3-bucket-name',
        )
        self.check_s3_vars(instance.get_storage_settings())
        appserver = make_test_appserver(instance)
        self.check_s3_vars(appserver.configuration_settings)


def get_s3_settings_profile_image(instance):
    """
    Return expected s3 settings related to profile image backend
    """
    s3_settings = (
        '\n  class: storages.backends.s3boto.S3BotoStorage'
        '\n  options:'
        '\n    headers:'
        '\n      Cache-Control: max-age-{{{{ EDXAPP_PROFILE_IMAGE_MAX_AGE }}}}'
        '\n    location: {instance.swift_container_name}/profile-images'
    ).format(instance=instance)

    return s3_settings


def get_s3_settings(instance):
    """
    Return expected s3 settings
    """
    s3_settings = {
        "COMMON_ENABLE_AWS_INTEGRATION": 'true',
        "COMMON_ENABLE_AWS_ROLE": 'true',
        "AWS_ACCESS_KEY_ID": instance.s3_access_key,
        "AWS_SECRET_ACCESS_KEY": instance.s3_secret_access_key,

        "EDXAPP_AWS_LOCATION": instance.swift_container_name,
        "EDXAPP_DEFAULT_FILE_STORAGE": 'storages.backends.s3boto.S3BotoStorage',
        "EDXAPP_AWS_ACCESS_KEY_ID": instance.s3_access_key,
        "EDXAPP_AWS_SECRET_ACCESS_KEY": instance.s3_secret_access_key,
        "EDXAPP_AUTH_EXTRA": '\n  AWS_STORAGE_BUCKET_NAME: test\nEDXAPP_AWS_ACCESS_KEY_ID: test',
        "EDXAPP_AWS_S3_CUSTOM_DOMAIN": "{}.s3.{}.amazonaws.com".format(
            instance.s3_bucket_name,
            instance.s3_region or 'us-east-1'
        ),
        "EDXAPP_IMPORT_EXPORT_BUCKET": instance.s3_bucket_name,
        "EDXAPP_FILE_UPLOAD_BUCKET_NAME": instance.s3_bucket_name,
        "EDXAPP_FILE_UPLOAD_STORAGE_PREFIX": '{}/{}'.format(
            instance.swift_container_name,
            'submissions_attachments'
        ),
        "EDXAPP_GRADE_STORAGE_CLASS": 'storages.backends.s3boto.S3BotoStorage',
        "EDXAPP_GRADE_STORAGE_TYPE": 's3',
        "EDXAPP_GRADE_BUCKET": instance.s3_bucket_name,
        "EDXAPP_GRADE_ROOT_PATH": '{}/{}'.format(instance.swift_container_name, 'grades-download'),
        "EDXAPP_GRADE_STORAGE_KWARGS": (
            '\n  bucket: test\n  location: {}/grades-download'.format(
                instance.swift_container_name
            )
        ),
        "XQUEUE_AWS_ACCESS_KEY_ID": instance.s3_access_key,
        "XQUEUE_AWS_SECRET_ACCESS_KEY": instance.s3_secret_access_key,
        "XQUEUE_UPLOAD_BUCKET": instance.s3_bucket_name,
        "XQUEUE_UPLOAD_PATH_PREFIX": '{}/{}'.format(instance.swift_container_name, 'xqueue'),

        "COMMON_OBJECT_STORE_LOG_SYNC": 'true',
        "COMMON_OBJECT_STORE_LOG_SYNC_BUCKET": instance.s3_bucket_name,
        "COMMON_OBJECT_STORE_LOG_SYNC_PREFIX": '{}/{}'.format(instance.swift_container_name, 'logs/tracking/'),
        "AWS_S3_LOGS": 'true',
        "AWS_S3_LOGS_ACCESS_KEY_ID": instance.s3_access_key,
        "AWS_S3_LOGS_SECRET_KEY": instance.s3_secret_access_key,

        "EDXAPP_PROFILE_IMAGE_BACKEND": get_s3_settings_profile_image(instance),
    }

    if instance.s3_region:
        s3_settings.update({
            "aws_region": instance.s3_region,
        })

    return s3_settings


def get_swift_settings(instance):
    """
    Return expected Swift settings
    """
    return {
        'EDXAPP_DEFAULT_FILE_STORAGE': 'swift.storage.SwiftStorage',
        'EDXAPP_SWIFT_USERNAME': instance.swift_openstack_user,
        'EDXAPP_SWIFT_KEY': instance.swift_openstack_password,
        'EDXAPP_SWIFT_TENANT_NAME': instance.swift_openstack_tenant,
        'EDXAPP_SWIFT_AUTH_URL': instance.swift_openstack_auth_url,
        'EDXAPP_SWIFT_REGION_NAME': instance.swift_openstack_region,
        'EDXAPP_FILE_UPLOAD_STORAGE_BUCKET_NAME': instance.swift_container_name,

        'XQUEUE_SWIFT_USERNAME': instance.swift_openstack_user,
        'XQUEUE_SWIFT_KEY': instance.swift_openstack_password,
        'XQUEUE_SWIFT_TENANT_NAME': instance.swift_openstack_tenant,
        'XQUEUE_SWIFT_AUTH_URL': instance.swift_openstack_auth_url,
        'XQUEUE_SWIFT_REGION_NAME': instance.swift_openstack_region,
        'XQUEUE_UPLOAD_BUCKET': instance.swift_container_name,

        'SWIFT_LOG_SYNC_USERNAME': instance.swift_openstack_user,
        'SWIFT_LOG_SYNC_PASSWORD': instance.swift_openstack_password,
        'SWIFT_LOG_SYNC_TENANT_NAME': instance.swift_openstack_tenant,
        'SWIFT_LOG_SYNC_AUTH_URL': instance.swift_openstack_auth_url,
        'SWIFT_LOG_SYNC_REGION_NAME': instance.swift_openstack_region,
        'COMMON_OBJECT_STORE_LOG_SYNC_BUCKET': instance.swift_container_name,
    }


class ContainerTestCase(TestCase):
    """
    Tests for provisioning settings
    """
    def check_ansible_settings(self, appserver, expected=True, s3=False):
        """
        Verify the Ansible settings.
        """
        instance = appserver.instance
        if s3:
            expected_settings = get_s3_settings(instance)
        else:
            expected_settings = get_swift_settings(instance)

        # Replace any \' occurrences because some settings may have it while we do a blanket assertion without it.
        # For example: we assert "EDXAPP_SWIFT_TENANT_NAME: 9999999999" is in `ansible_vars`, which would have
        # "EDXAPP_SWIFT_TENANT_NAME: \'9999999999\'", causing a mismatch unless we strip the \'.
        ansible_vars = str(appserver.configuration_settings).replace("\'", '')
        for ansible_var, value in expected_settings.items():
            if expected:
                self.assertRegex(ansible_vars, r'{}:\s*{}'.format(ansible_var, value))
            else:
                self.assertNotRegex(ansible_vars, r'{}:\s*{}'.format(ansible_var, value))


@ddt.ddt
@patch(
    'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class SwiftContainerInstanceTestCase(ContainerTestCase):
    """
    Tests for Swift container provisioning.
    """

    def check_swift(self, instance, create_swift_container):
        """
        Verify Swift settings on the instance and the number of calls to the Swift API.
        """
        self.assertIs(instance.swift_provisioned, True)
        self.assertEqual(instance.swift_openstack_user, settings.SWIFT_OPENSTACK_USER)
        self.assertEqual(instance.swift_openstack_password, settings.SWIFT_OPENSTACK_PASSWORD)
        self.assertEqual(instance.swift_openstack_tenant, settings.SWIFT_OPENSTACK_TENANT)
        self.assertEqual(instance.swift_openstack_auth_url, settings.SWIFT_OPENSTACK_AUTH_URL)
        self.assertEqual(instance.swift_openstack_region, settings.SWIFT_OPENSTACK_REGION)

        def make_call(container_name):
            """A helper method to prepare mock.call."""
            return call(
                container_name,
                user=instance.swift_openstack_user,
                password=instance.swift_openstack_password,
                tenant=instance.swift_openstack_tenant,
                auth_url=instance.swift_openstack_auth_url,
                region=instance.swift_openstack_region,
            )

        self.assertCountEqual(
            [make_call(container) for container in instance.swift_container_names],
            create_swift_container.call_args_list,
        )

    @patch('instance.openstack_utils.create_swift_container')
    def test_provision_swift(self, create_swift_container, mock_consul):
        """
        Test provisioning Swift containers, and that they are provisioned only once.
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.SWIFT_STORAGE
        instance.provision_swift()
        self.check_swift(instance, create_swift_container)

        # Reset the mock, and provision again.  The container is technically reprovisioned, but this is a no-op.
        create_swift_container.reset_mock()
        instance.provision_swift()
        self.check_swift(instance, create_swift_container)

    @patch('instance.openstack_utils.create_swift_container')
    def test_deprovision_swift(self, create_swift_container, mock_consul):
        """
        Test deprovisioning Swift containers.
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.SWIFT_STORAGE
        instance.provision_swift()
        self.check_swift(instance, create_swift_container)
        instance.deprovision_swift()
        self.assertIs(instance.swift_provisioned, False)

    @patch('instance.openstack_utils.create_swift_container')
    def test_swift_disabled(self, create_swift_container, mock_consul):
        """
        Verify disabling Swift provisioning works.
        """
        instance = OpenEdXInstanceFactory()
        instance.provision_swift()
        self.assertIs(instance.swift_provisioned, False)
        self.assertFalse(create_swift_container.called)

    @override_settings(INSTANCE_STORAGE_TYPE='swift')
    def test_ansible_settings_swift(self, mock_consul):
        """
        Verify Swift Ansible configuration when Swift is enabled.
        """
        instance = OpenEdXInstanceFactory()
        appserver = make_test_appserver(instance)
        self.check_ansible_settings(appserver)

    def test_ansible_settings_swift_disabled(self, mock_consul):
        """
        Verify Swift Ansible configuration is not included when Swift is disabled.
        """
        instance = OpenEdXInstanceFactory()
        appserver = make_test_appserver(instance)
        self.check_ansible_settings(appserver, expected=False)


@ddt.ddt
@override_settings(
    AWS_ACCESS_KEY='test',
    AWS_SECRET_ACCESS_KEY_ID='test',
)
@patch(
    'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class S3ContainerInstanceTestCase(ContainerTestCase):
    """
    Tests for S3 Storage
    """
    default_region = boto3.client('s3').meta.config.region_name

    @ddt.data(
        '',
        'eu-west-1',
    )
    def test_ansible_settings_s3(self, s3_region, mock_consul):
        """
        Verify S3 Ansible configuration when S3 is enabled.
        """
        instance = OpenEdXInstanceFactory()
        instance.s3_region = s3_region
        appserver = make_test_appserver(instance, s3=True)
        self.check_ansible_settings(appserver, s3=True)

    @ddt.data(
        ('', default_region),
        ('region', 'region'),
        ('eu-central-1', 'eu-central-1'),
    )
    @ddt.unpack
    def test_get_s3_connection(self, s3_region, expected_region, mock_consul):
        """
        Test get_s3 connection returns right instance
        """
        instance = OpenEdXInstanceFactory()
        instance.s3_region = s3_region
        self.assertEqual(instance.s3.meta.region_name, expected_region)

    def test_get_s3_policy(self, mock_consul):
        """
        Verify S3 policy is set for correctly
        """
        instance = OpenEdXInstanceFactory(s3_bucket_name='test_bucket')
        actions = [
            "s3:ListBucket",
            "s3:CreateBucket",
            "s3:DeleteBucket",
            "s3:PutBucketCORS",
            "s3:PutBucketVersioning",
            "s3:PutLifecycleConfiguration",
        ]
        policy = instance.get_s3_policy()['Statement']
        self.assertIn("arn:aws:s3:::{}".format(instance.s3_bucket_name), policy[0]['Resource'])
        for action in actions:
            self.assertIn(action, policy[0]['Action'])

    @ddt.data(
        (True, ), (False, )
    )
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    def test_provision_s3(self, provision_iam, mock_consul):
        """
        Test s3 provisioning succeeds
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE
        instance.s3_bucket_name = 'test'
        instance.s3_region = 'test'
        if not provision_iam:
            instance.s3_access_key = 'test'
            instance.s3_secret_access_key = 'test'

        with S3Stubber(s3_client) as stubber, IAMStubber(iam_client) as iamstubber:
            if provision_iam:
                iamstubber.stub_create_user(instance.iam_username)
                iamstubber.stub_create_access_key(instance.iam_username)
                iamstubber.stub_put_user_policy(
                    instance.iam_username,
                    storage.USER_POLICY_NAME,
                    instance.get_s3_policy()
                )
                stubber.stub_create_bucket()
                stubber.stub_put_cors()
                stubber.stub_set_expiration()
                stubber.stub_versioning()
                instance.provision_s3()

    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    def test__create_bucket_fails(self, mock_consul):
        """
        Test s3 provisioning fails on bucket creation, and retries up to 4 times
        """
        instance = OpenEdXInstanceFactory()
        instance.s3_access_key = 'test'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        max_tries = 4
        stubber = Stubber(s3_client)
        for _ in range(max_tries):
            stubber.add_client_error('create_bucket')
        with self.assertLogs('instance.models.instance', level='INFO') as cm:
            with stubber:
                with self.assertRaises(ClientError):
                    instance._create_bucket(max_tries=max_tries)

            base_log_text = (
                'INFO:instance.models.instance:instance={} ({!s:.15}) | Retrying bucket creation'
                ' due to "", attempt %s of {}.'.format(instance.ref.pk, instance.ref.name, max_tries)
            )
            self.assertEqual(
                cm.output,
                [base_log_text % i for i in range(1, max_tries + 1)]
            )

    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    def test__update_bucket_fails(self, mock_consul):
        """
        Test s3 provisioning fails on bucket update, and retries up to 4 times
        This can happen when the IAM is updated but the propagation is delayed
        """
        instance = OpenEdXInstanceFactory()
        instance.s3_access_key = 'test'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        max_tries = 4
        stubber = S3Stubber(s3_client)
        stubber.stub_create_bucket(location='')
        for _ in range(max_tries):
            stubber.stub_put_cors()
            stubber.add_client_error('put_bucket_lifecycle_configuration')
        with self.assertLogs('instance.models.instance', level='INFO') as cm:
            with stubber, self.assertRaises(ClientError):
                instance._create_bucket(max_tries=max_tries)

            base_log_text = (
                'INFO:instance.models.instance:instance={} ({!s:.15}) | Retrying bucket configuration'
                ' due to "", attempt %s of {}.'.format(instance.ref.pk, instance.ref.name, max_tries)
            )
            for i in range(1, 1 + max_tries):
                self.assertIn(
                    base_log_text % i,
                    cm.output,
                )

    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    def test_deprovision_s3(self, mock_consul):
        """
        Test s3 deprovisioning succeeds
        """

        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE
        instance.s3_access_key = 'test_0123456789a'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        instance.s3_region = 'test'
        instance.save()

        with S3Stubber(s3_client) as stubber, IAMStubber(iam_client) as iamstubber:
            iamstubber.stub_put_user_policy(
                instance.iam_username,
                storage.USER_POLICY_NAME,
                instance.get_s3_policy()
            )
            stubber.stub_create_bucket()
            stubber.stub_put_cors()
            stubber.stub_set_expiration()
            stubber.stub_versioning()
            instance.provision_s3()
            # Put an object
            stubber.stub_put_object(b'test', 'test')
            s3_client.put_object(Body=b'test', Bucket='test', Key='test')
            # Overwrite object
            stubber.stub_put_object(b'another_test', 'test')
            s3_client.put_object(Body=b'another_test', Bucket='test', Key='test')
            # Put another object
            stubber.stub_put_object(b'another_test', 'another_test')
            s3_client.put_object(Body=b'another_test', Bucket='test', Key='another_test')
            # Delete object
            stubber.stub_delete_object(key='another_test')
            s3_client.delete_object(Bucket='test', Key='another_test')
            # Make sure three versions and a delete marker are removed
            items = {
                'Versions': [
                    {'Key': 'test', 'VersionId': '1a'},
                    {'Key': 'test', 'VersionId': '2b'},
                    {'Key': 'another_test', 'VersionId': '3c'}
                ],
                'DeleteMarkers': [
                    {'Key': 'another_test', 'VersionId': '4d'}
                ]
            }
            stubber.stub_list_object_versions(result=items)
            stubber.add_response('delete_objects', {}, {
                'Bucket': 'test',
                'Delete': {
                    'Objects': [{'Key': d['Key'], 'VersionId': d['VersionId']}
                                for d in items['Versions'] + items['DeleteMarkers']]
                }
            })
            stubber.stub_list_object_versions(result={})
            stubber.stub_delete_bucket()

            iamstubber.stub_delete_access_key(instance.iam_username, instance.s3_access_key)
            iamstubber.stub_delete_user_policy(instance.iam_username)
            iamstubber.stub_delete_user(instance.iam_username)
            instance.deprovision_s3()

        instance.refresh_from_db()
        self.assertEqual(instance.s3_bucket_name, "")
        self.assertEqual(instance.s3_access_key, "")
        self.assertEqual(instance.s3_secret_access_key, "")
        # We always want to preserve information about a client's preferred region, so s3_region should not be empty.
        self.assertEqual(instance.s3_region, "test")

    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    def test_deprovision_s3_delete_user_fails(self, mock_consul):
        """
        Test s3 deprovisioning fails on delete_user
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE
        instance.s3_access_key = 'test_0123456789a'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        instance.save()

        with self.assertLogs("instance.models.instance"):
            with S3Stubber(s3_client) as stubber, IAMStubber(iam_client) as iamstubber:
                iamstubber.stub_put_user_policy(
                    instance.iam_username,
                    storage.USER_POLICY_NAME,
                    instance.get_s3_policy()
                )
                stubber.stub_create_bucket(location='')
                stubber.stub_put_cors()
                stubber.stub_set_expiration()
                stubber.stub_versioning()
                instance.provision_s3()

                stubber.stub_list_object_versions(result={})
                stubber.stub_delete_bucket()

                iamstubber.stub_delete_access_key(instance.iam_username, instance.s3_access_key)
                iamstubber.stub_delete_user_policy(instance.iam_username)
                iamstubber.add_client_error('delete_user')

                with self.assertRaises(ClientError):
                    instance.deprovision_s3()

        # Since it failed deleting the user, access_keys should not be empty.
        instance.refresh_from_db()
        self.assertEqual(instance.s3_access_key, "test_0123456789a")
        self.assertEqual(instance.s3_secret_access_key, "test")

    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    def test_deprovision_s3_user_does_not_exist(self, mock_consul):
        """
        Test s3 deprovisioning when AIM user does not exist
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE
        instance.s3_access_key = 'test_0123456789a'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        instance.save()

        with self.assertLogs("instance.models.instance"):
            with S3Stubber(s3_client) as stubber, IAMStubber(iam_client) as iamstubber:
                iamstubber.stub_put_user_policy(
                    instance.iam_username,
                    storage.USER_POLICY_NAME,
                    instance.get_s3_policy()
                )
                stubber.stub_create_bucket(location='')
                stubber.stub_put_cors()
                stubber.stub_set_expiration()
                stubber.stub_versioning()
                instance.provision_s3()

                stubber.stub_list_object_versions(result={})
                stubber.stub_delete_bucket()

                iamstubber.add_client_error('delete_access_key', service_error_code='NoSuchEntity')
                iamstubber.add_client_error('delete_user_policy', service_error_code='NoSuchEntity')
                iamstubber.add_client_error('delete_user', service_error_code='NoSuchEntity')
                instance.deprovision_s3()

        # Since the user and associated acess key and policy don't exist,
        # the fields should be blanked out.
        instance.refresh_from_db()
        self.assertEqual(instance.s3_access_key, "")
        self.assertEqual(instance.s3_secret_access_key, "")

    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    def test_deprovision_s3_delete_bucket_fails(self, mock_consul):
        """
        Test s3 deprovisioning fails on delete_bucket
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE
        instance.s3_access_key = 'test_0123456789a'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        instance.s3_region = 'test'
        instance.save()

        with self.assertLogs("instance.models.instance"):
            with S3Stubber(s3_client) as stubber, IAMStubber(iam_client) as iamstubber:
                iamstubber.stub_put_user_policy(
                    instance.iam_username,
                    storage.USER_POLICY_NAME,
                    instance.get_s3_policy()
                )
                stubber.stub_create_bucket()
                stubber.stub_put_cors()
                stubber.stub_set_expiration()
                stubber.stub_versioning()

                instance.provision_s3()

                stubber.stub_list_object_versions(result={})
                stubber.add_client_error('delete_bucket')

                iamstubber.stub_delete_access_key(instance.iam_username, instance.s3_access_key)
                iamstubber.stub_delete_user_policy(instance.iam_username)
                iamstubber.stub_delete_user(instance.iam_username)

                with self.assertRaises(ClientError):
                    instance.deprovision_s3()

        instance.refresh_from_db()
        # Since it failed deleting the bucket, all S3 related information should be left intact.
        self.assertEqual(instance.s3_bucket_name, "test")
        self.assertEqual(instance.s3_region, "test")
        self.assertEqual(instance.s3_access_key, "test_0123456789a")
        self.assertEqual(instance.s3_secret_access_key, "test")

    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    def test_deprovision_s3_bucket_does_not_exist(self, mock_consul):
        """
        Test s3 deprovisioning when s3 bucket does not exist
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE
        instance.s3_access_key = 'test_0123456789a'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        instance.s3_region = 'test'
        instance.save()

        with self.assertLogs("instance.models.instance"):
            with S3Stubber(s3_client) as stubber, IAMStubber(iam_client) as iamstubber:
                iamstubber.stub_put_user_policy(
                    instance.iam_username,
                    storage.USER_POLICY_NAME,
                    instance.get_s3_policy()
                )
                stubber.stub_create_bucket()
                stubber.stub_put_cors()
                stubber.stub_set_expiration()
                stubber.stub_versioning()
                instance.provision_s3()

                stubber.stub_list_object_versions(result={})
                stubber.add_client_error('delete_bucket', service_error_code='NoSuchBucket')

                iamstubber.stub_delete_access_key(instance.iam_username, instance.s3_access_key)
                iamstubber.stub_delete_user_policy(instance.iam_username)
                iamstubber.stub_delete_user(instance.iam_username)
                instance.deprovision_s3()

        instance.refresh_from_db()
        # Since the bucket does not exists, the s3_bucket_name field should be blanked out.
        self.assertEqual(instance.s3_bucket_name, "")

    @override_settings(AWS_S3_DEFAULT_REGION='test')
    def test_provision_s3_swift(self, mock_consul):
        """
        Test s3 provisioning does nothing when SWIFT is enabled
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.SWIFT_STORAGE
        instance.provision_s3()
        instance.refresh_from_db()
        self.assertEqual(instance.s3_bucket_name, '')
        self.assertEqual(instance.s3_access_key, '')
        self.assertEqual(instance.s3_secret_access_key, '')
        self.assertEqual(instance.s3_region, settings.AWS_S3_DEFAULT_REGION)

    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.s3', s3_client)
    def test_provision_s3_unconfigured(self, mock_consul):
        """
        Test s3 provisioning works with default bucket and IAM
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE
        instance.s3_bucket_name = instance.bucket_name  # For stubbing to work correctly
        with S3Stubber(s3_client) as stubber, IAMStubber(iam_client) as iamstubber:
            iamstubber.stub_create_user(instance.iam_username)
            iamstubber.stub_create_access_key(instance.iam_username)
            iamstubber.stub_put_user_policy(
                instance.iam_username,
                storage.USER_POLICY_NAME,
                instance.get_s3_policy()
            )
            stubber.stub_create_bucket(bucket=instance.s3_bucket_name, location='')
            stubber.stub_put_cors(bucket=instance.s3_bucket_name)
            stubber.stub_set_expiration(bucket=instance.s3_bucket_name)
            stubber.stub_versioning(bucket=instance.s3_bucket_name)
            instance.provision_s3()
        instance.refresh_from_db()
        self.assertIsNotNone(instance.s3_bucket_name)
        self.assertIsNotNone(instance.s3_access_key)
        self.assertIsNotNone(instance.s3_secret_access_key)
        self.assertEqual(instance.s3_region, settings.AWS_S3_DEFAULT_REGION)
        self.assertEqual(instance.s3_hostname, settings.AWS_S3_DEFAULT_HOSTNAME)

    @override_settings(AWS_ACCESS_KEY_ID='test_0123456789a', AWS_SECRET_ACCESS_KEY='secret')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    def test_create_iam_user(self, mock_consul):
        """
        Test create_iam_user succeeds and sets the required attributes
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE

        with IAMStubber(iam_client) as iamstubber:
            iamstubber.stub_create_user(instance.iam_username)
            iamstubber.stub_create_access_key(instance.iam_username)
            iamstubber.stub_put_user_policy(
                instance.iam_username,
                storage.USER_POLICY_NAME,
                instance.get_s3_policy()
            )
            instance.create_iam_user()
            instance.refresh_from_db()
            self.assertEqual(instance.s3_access_key, 'test_0123456789a')
            self.assertEqual(instance.s3_secret_access_key, 'secret')

    @override_settings(AWS_ACCESS_KEY_ID='test_0123456789a', AWS_SECRET_ACCESS_KEY='secret')
    @patch('instance.models.mixins.storage.S3BucketInstanceMixin.iam', iam_client)
    def test_iam_user_exists(self, mock_consul):
        """
        Test create_iam_user succeeds when user already exists
        """
        instance = OpenEdXInstanceFactory()
        instance.storage_type = StorageContainer.S3_STORAGE

        with IAMStubber(iam_client) as iamstubber:
            iamstubber.add_client_error('create_user', 'EntityAlreadyExists')
            iamstubber.stub_create_access_key(instance.iam_username)
            iamstubber.stub_put_user_policy(
                instance.iam_username,
                storage.USER_POLICY_NAME,
                instance.get_s3_policy()
            )
            instance.create_iam_user()
            instance.refresh_from_db()
            self.assertEqual(instance.s3_access_key, 'test_0123456789a')
            self.assertEqual(instance.s3_secret_access_key, 'secret')

    def test_get_s3_cors(self, mock_consul):
        """
        Test get_s3_config succeeds
        """
        self.assertEqual(S3_CORS['CORSRules'][0]['AllowedMethods'], ['GET', 'PUT'])
        self.assertEqual(S3_CORS['CORSRules'][0]['AllowedHeaders'], ['*'])
        self.assertEqual(S3_CORS['CORSRules'][0]['AllowedOrigins'], ['*'])

    def test_bucket_name(self, mock_consul):
        """
        Test bucket_name is correct
        """
        instance = OpenEdXInstanceFactory()
        self.assertRegex(instance.bucket_name, r'ocim-instance[A-Za-z0-9]*-test-example-com')

    def test_iam_username(self, mock_consul):
        """
        Test bucket_name is correct
        """
        instance = OpenEdXInstanceFactory()
        self.assertRegex(instance.iam_username, r'ocim-instance[A-Za-z0-9]*_test_example_com')

    def test_s3_region_default_value(self, mock_consul):
        """
        Test the default value for the S3 region
        """
        instance = OpenEdXInstanceFactory()
        self.assertEqual(instance.s3_region, settings.AWS_S3_DEFAULT_REGION)
