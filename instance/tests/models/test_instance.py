# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
SingleVMOpenEdXInstance model - Tests
"""

# Imports #####################################################################

from urllib.parse import urlparse

import re
import yaml
from django.conf import settings
from django.test import override_settings
from mock import call, patch, Mock

from instance.models.instance import InconsistentInstanceState, Instance, SingleVMOpenEdXInstance
from instance.models.server import Server, Progress as ServerProgress
from instance.tests.base import TestCase
from instance.tests.factories.pr import PRFactory
from instance.tests.models.factories.instance import SingleVMOpenEdXInstanceFactory
from instance.tests.models.factories.server import BuildingOpenStackServerFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

# Factory boy doesn't properly support pylint+django
#pylint: disable=no-member


class InstanceTestCase(TestCase):
    """
    Test cases for instance models
    """
    def test_new_instance(self):
        """
        New SingleVMOpenEdXInstance object
        """
        self.assertFalse(SingleVMOpenEdXInstance.objects.all())
        instance = SingleVMOpenEdXInstanceFactory()
        self.assertEqual(SingleVMOpenEdXInstance.objects.get().pk, instance.pk)
        self.assertTrue(re.search(r'Test Instance \d+ \(http://instance\d+\.test\.example\.com/\)', str(instance)))

    def test_domain_url(self):
        """
        Domain and URL attributes
        """
        instance = SingleVMOpenEdXInstanceFactory(
            base_domain='example.org', sub_domain='sample', name='Sample Instance'
        )
        self.assertEqual(instance.domain, 'sample.example.org')
        self.assertEqual(instance.url, 'http://sample.example.org/')
        self.assertEqual(instance.studio_domain, 'studio.sample.example.org')
        self.assertEqual(instance.studio_url, 'http://studio.sample.example.org/')
        self.assertEqual(str(instance), 'Sample Instance (http://sample.example.org/)')

    def test_commit_short_id(self):
        """
        Short representation of a commit_id
        """
        instance = SingleVMOpenEdXInstanceFactory(commit_id='6e580ca9fed6fb65ec45949494dabec40e8cb533')
        self.assertEqual(instance.commit_short_id, '6e580ca')
        instance.commit_id = None
        self.assertEqual(instance.commit_short_id, None)

    def test_status(self):
        """
        Instance status with one active server
        """
        instance = SingleVMOpenEdXInstanceFactory()
        self.assertIsNone(instance.server_status)
        self.assertIsNone(instance.progress)
        server = BuildingOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.server_status, Server.Status.Building)
        self.assertEqual(instance.progress, Server.Progress.Running)
        server._transition(server._status_to_booting)
        self.assertEqual(instance.server_status, Server.Status.Booting)
        server._transition(server._status_to_ready)
        self.assertEqual(instance.server_status, Server.Status.Ready)

    def test_status_terminated(self):
        """
        Instance status should revert to 'empty' when all its servers are terminated
        """
        instance = SingleVMOpenEdXInstanceFactory()
        server = BuildingOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.server_status, server.Status.Building)
        server._transition(server._status_to_terminated)
        self.assertIsNone(instance.server_status)

    def test_status_multiple_servers(self):
        """
        Instance status should not allow multiple active servers
        """
        instance = SingleVMOpenEdXInstanceFactory()
        BuildingOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.server_status, Server.Status.Building)
        self.assertEqual(instance.progress, Server.Progress.Running)
        BuildingOpenStackServerFactory(instance=instance)
        with self.assertRaises(InconsistentInstanceState):
            instance.server_status #pylint: disable=pointless-statement


@patch('instance.openstack.SwiftConnection')
class SwiftContainerInstanceTestCase(TestCase):
    """
    Tests for Swift container provisioning.
    """
    def check_swift(self, instance, mock_swift_connection):
        """
        Verify Swift settings on the instance and the number of calls to the Swift API.
        """
        self.assertIs(instance.swift_provisioned, True)
        self.assertEqual(instance.swift_openstack_user, settings.SWIFT_OPENSTACK_USER)
        self.assertEqual(instance.swift_openstack_password, settings.SWIFT_OPENSTACK_PASSWORD)
        self.assertEqual(instance.swift_openstack_tenant, settings.SWIFT_OPENSTACK_TENANT)
        self.assertEqual(instance.swift_openstack_auth_url, settings.SWIFT_OPENSTACK_AUTH_URL)
        self.assertEqual(instance.swift_openstack_region, settings.SWIFT_OPENSTACK_REGION)
        self.assertCountEqual(
            [call(c, headers={'X-Container-Read': '.r:*'}) for c in instance.swift_container_names],
            mock_swift_connection.return_value.put_container.call_args_list,
        )

    def test_provision_swift(self, mock_swift_connection):
        """
        Test provisioning Swift containers, and that they are provisioned only once.
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_swift()
        self.check_swift(instance, mock_swift_connection)

        # Provision again without resetting the mock.  The assertCountEqual assertion will verify
        # that the container isn't provisioned again.
        instance.provision_swift()
        self.check_swift(instance, mock_swift_connection)

    @override_settings(SWIFT_ENABLE=False)
    def test_swift_disabled(self, mock_swift_connection):
        """
        Verify disabling Swift provisioning works.
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_swift()
        self.assertIs(instance.swift_provisioned, False)
        self.assertFalse(mock_swift_connection.called)


class SingleVMOpenEdXInstanceTestCase(TestCase):
    """
    Test cases for SingleVMOpenEdXInstance models
    """
    @override_settings(INSTANCE_EPHEMERAL_DATABASES=False)
    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    def test_create_defaults(self, mock_get_commit_id_from_ref):
        """
        Create an instance without specifying additional fields,
        leaving it up to the create method to set them
        """
        mock_get_commit_id_from_ref.return_value = '9' * 40
        instance = SingleVMOpenEdXInstance.objects.create(sub_domain='create.defaults')
        self.assertEqual(instance.github_organization_name, 'edx')
        self.assertEqual(instance.github_repository_name, 'edx-platform')
        self.assertEqual(instance.commit_id, '9' * 40)
        self.assertEqual(instance.name, 'edx/master (9999999)')
        self.assertFalse(instance.mysql_user)
        self.assertFalse(instance.mysql_pass)
        self.assertFalse(instance.mongo_user)
        self.assertFalse(instance.mongo_pass)
        self.assertFalse(instance.swift_openstack_user)
        self.assertFalse(instance.swift_openstack_password)
        self.assertFalse(instance.swift_openstack_tenant)
        self.assertFalse(instance.swift_openstack_auth_url)
        self.assertFalse(instance.swift_openstack_region)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=True)
    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    def test_create_from_pr(self, mock_get_commit_id_from_ref):
        """
        Create an instance from a pull request
        """
        mock_get_commit_id_from_ref.return_value = '9' * 40
        pr = PRFactory()
        instance, created = SingleVMOpenEdXInstance.objects.update_or_create_from_pr(pr, sub_domain='test.sandbox')
        self.assertTrue(created)
        self.assertEqual(instance.fork_name, pr.fork_name)
        self.assertEqual(instance.branch_name, pr.branch_name)
        self.assertRegex(instance.name, r'^PR')
        self.assertEqual(instance.github_pr_number, pr.number)
        self.assertIs(instance.use_ephemeral_databases, True)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=False)
    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    def test_create_from_pr_ephemeral_databases(self, mock_get_commit_id_from_ref):
        """
        Instances should use ephemeral databases if requested in the PR
        """
        mock_get_commit_id_from_ref.return_value = '9' * 40
        pr = PRFactory(body='test.sandbox.example.com (ephemeral databases)')
        instance, _ = SingleVMOpenEdXInstance.objects.update_or_create_from_pr(pr, sub_domain='test.sandbox')
        self.assertIs(instance.use_ephemeral_databases, True)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=True)
    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    def test_create_from_pr_persistent_databases(self, mock_get_commit_id_from_ref):
        """
        Instances should use persistent databases if requested in the PR
        """
        mock_get_commit_id_from_ref.return_value = '9' * 40
        pr = PRFactory(body='test.sandbox.example.com (persistent databases)')
        instance, _ = SingleVMOpenEdXInstance.objects.update_or_create_from_pr(pr, sub_domain='test.sandbox')
        self.assertIs(instance.use_ephemeral_databases, False)

    def test_get_by_fork_name(self):
        """
        Use `fork_name` to get an instance object from the ORM
        """
        SingleVMOpenEdXInstanceFactory(
            github_organization_name='get-by',
            github_repository_name='fork-name',
        )
        instance = SingleVMOpenEdXInstance.objects.get(fork_name='get-by/fork-name')
        self.assertEqual(instance.fork_name, 'get-by/fork-name')

    def test_ansible_s3_settings(self):
        """
        Add extra settings in ansible vars, which can override existing settings
        """
        instance = SingleVMOpenEdXInstanceFactory(
            s3_access_key='test-s3-access-key',
            s3_secret_access_key='test-s3-secret-access-key',
            s3_bucket_name='test-s3-bucket-name',
        )
        instance.reset_ansible_settings()
        self.assertIn('AWS_ACCESS_KEY_ID: test-s3-access-key', instance.ansible_settings)
        self.assertIn('AWS_SECRET_ACCESS_KEY: test-s3-secret-access-key', instance.ansible_settings)
        self.assertIn('EDXAPP_AUTH_EXTRA: {AWS_STORAGE_BUCKET_NAME: test-s3-bucket-name}', instance.ansible_settings)
        self.assertIn('EDXAPP_AWS_ACCESS_KEY_ID: test-s3-access-key', instance.ansible_settings)
        self.assertIn('EDXAPP_AWS_SECRET_ACCESS_KEY: test-s3-secret-access-key', instance.ansible_settings)
        self.assertIn('XQUEUE_AWS_ACCESS_KEY_ID: test-s3-access-key', instance.ansible_settings)
        self.assertIn('XQUEUE_AWS_SECRET_ACCESS_KEY: test-s3-secret-access-key', instance.ansible_settings)
        self.assertIn('XQUEUE_S3_BUCKET: test-s3-bucket-name', instance.ansible_settings)

    @override_settings(INSTANCE_MYSQL_URL_OBJ=urlparse('mysql://user:pass@mysql.opencraft.com'))
    def test_ansible_settings_mysql(self):
        """
        Add mysql ansible vars if INSTANCE_MYSQL_URL is set
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.reset_ansible_settings()
        self.assertIn('EDXAPP_MYSQL_USER: {0}'.format(instance.mysql_user), instance.ansible_settings)
        self.assertIn('EDXAPP_MYSQL_PASSWORD: {0}'.format(instance.mysql_pass), instance.ansible_settings)
        self.assertIn('EDXAPP_MYSQL_HOST: mysql.opencraft.com', instance.ansible_settings)
        self.assertIn('EDXAPP_MYSQL_PORT: 3306', instance.ansible_settings)
        self.assertIn('EDXAPP_MYSQL_DB_NAME: {0}'.format(instance.mysql_database_name), instance.ansible_settings)
        self.assertIn('COMMON_MYSQL_MIGRATE_USER: {0}'.format(instance.mysql_user), instance.ansible_settings)
        self.assertIn('COMMON_MYSQL_MIGRATE_PASS: {0}'.format(instance.mysql_pass), instance.ansible_settings)

    @override_settings(INSTANCE_MYSQL_URL_OBJ=None)
    def test_ansible_settings_mysql_not_set(self):
        """
        Don't add mysql ansible vars if INSTANCE_MYSQL_URL is not set
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.reset_ansible_settings()
        self.check_mysql_vars_not_set(instance)

    @override_settings(INSTANCE_MYSQL_URL_OBJ=urlparse('mysql://user:pass@mysql.opencraft.com'))
    def test_ansible_settings_mysql_ephemeral(self):
        """
        Don't add mysql ansible vars for ephemeral databases
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=True)
        instance.reset_ansible_settings()
        self.check_mysql_vars_not_set(instance)

    def check_mysql_vars_not_set(self, instance):
        """
        Check that the given instance does not point to a mysql database
        """
        for var in ('EDXAPP_MYSQL_USER',
                    'EDXAPP_MYSQL_PASSWORD',
                    'EDXAPP_MYSQL_HOST',
                    'EDXAPP_MYSQL_PORT',
                    'EDXAPP_MYSQL_DB_NAME',
                    'COMMON_MYSQL_MIGRATE_USER',
                    'COMMON_MYSQL_MIGRATE_PASS'):
            self.assertNotIn(var, instance.ansible_settings)

    @override_settings(INSTANCE_MONGO_URL_OBJ=urlparse('mongodb://user:pass@mongo.opencraft.com'))
    def test_ansible_settings_mongo(self):
        """
        Add mongo ansible vars if INSTANCE_MONGO_URL is set
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.reset_ansible_settings()
        self.assertIn('EDXAPP_MONGO_USER: {0}'.format(instance.mongo_user), instance.ansible_settings)
        self.assertIn('EDXAPP_MONGO_PASSWORD: {0}'.format(instance.mongo_pass), instance.ansible_settings)
        self.assertIn('EDXAPP_MONGO_HOSTS: [mongo.opencraft.com]', instance.ansible_settings)
        self.assertIn('EDXAPP_MONGO_PORT: 27017', instance.ansible_settings)
        self.assertIn('EDXAPP_MONGO_DB_NAME: {0}'.format(instance.mongo_database_name), instance.ansible_settings)
        self.assertIn('FORUM_MONGO_USER: {0}'.format(instance.mongo_user), instance.ansible_settings)
        self.assertIn('FORUM_MONGO_PASSWORD: {0}'.format(instance.mongo_pass), instance.ansible_settings)
        self.assertIn('FORUM_MONGO_HOSTS: [mongo.opencraft.com]', instance.ansible_settings)
        self.assertIn('FORUM_MONGO_PORT: 27017', instance.ansible_settings)
        self.assertIn('FORUM_MONGO_DATABASE: {0}'.format(instance.forum_database_name), instance.ansible_settings)

    @override_settings(INSTANCE_MONGO_URL_OBJ=None)
    def test_ansible_settings_mongo_not_set(self):
        """
        Don't add mongo ansible vars if INSTANCE_MONGO_URL is not set
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.reset_ansible_settings()
        self.check_mongo_vars_not_set(instance)

    @override_settings(INSTANCE_MONGO_URL_OBJ=urlparse('mongodb://user:pass@mongo.opencraft.com'))
    def test_ansible_settings_mongo_ephemeral(self):
        """
        Don't add mongo ansible vars if INSTANCE_MONGO_URL is not set
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=True)
        instance.reset_ansible_settings()
        self.check_mongo_vars_not_set(instance)

    def check_mongo_vars_not_set(self, instance):
        """
        Check that the given instance does not point to a mongo database
        """
        for var in ('EDXAPP_MONGO_USER',
                    'EDXAPP_MONGO_PASSWORD'
                    'EDXAPP_MONGO_HOSTS',
                    'EDXAPP_MONGO_PORT',
                    'EDXAPP_MONGO_DB_NAME',
                    'FORUM_MONGO_USER',
                    'FORUM_MONGO_PASSWORD',
                    'FORUM_MONGO_HOSTS',
                    'FORUM_MONGO_PORT',
                    'FORUM_MONGO_DATABASE'):
            self.assertNotIn(var, instance.ansible_settings)

    @patch_services
    def test_provision(self, mocks):
        """
        Run provisioning sequence
        """
        mocks.mock_deploy.return_value = (['log'], 0)
        mocks.mock_create_server.side_effect = [Mock(id='test-run-provisioning-server'), None]
        mocks.os_server_manager.add_fixture('test-run-provisioning-server', 'openstack/api_server_2_active.json')
        mock_reboot = mocks.os_server_manager.get_os_server('test-run-provisioning-server').reboot

        instance = SingleVMOpenEdXInstanceFactory(sub_domain='run.provisioning', use_ephemeral_databases=True)
        instance.provision()
        self.assertEqual(mocks.mock_set_dns_record.mock_calls, [
            call(name='run.provisioning', type='A', value='192.168.100.200'),
            call(name='studio.run.provisioning', type='CNAME', value='run.provisioning'),
        ])
        self.assertEqual(mocks.mock_deploy.call_count, 1)
        self.assertEqual(mock_reboot.call_count, 1)
        self.assertEqual(mocks.mock_provision_mysql.call_count, 0)
        self.assertEqual(mocks.mock_provision_mongo.call_count, 0)
        self.assertEqual(mocks.mock_provision_swift.call_count, 0)

    @patch_services
    def test_provision_failed(self, mocks):
        """
        Run provisioning sequence failing the deployment on purpose to make sure
        server and instance statuses will be set accordingly.
        """
        log_lines = ['log']
        mocks.mock_deploy.return_value = (log_lines, 1)
        instance = SingleVMOpenEdXInstanceFactory(sub_domain='run.provisioning', attempts=1)

        server = instance.provision()[0]
        self.assertEqual(instance.status, Instance.Status.ConfigurationFailed)
        self.assertEqual(server.status, Server.Status.Ready)
        mocks.mock_provision_failed_email.assert_called_once_with(instance.ProvisionMessages.PROVISION_ERROR, log_lines)
        mocks.mock_provision_failed_email.assert_called_once_with(instance.ProvisionMessages.PROVISION_ERROR, log_lines)

    @patch_services
    def test_provision_second_attempt(self, mocks):
        """
        Tests provisioning is retried if first attempt fails
        """
        mocks.mock_deploy.side_effect = [(['log'], 1), ([], 0)]
        mocks.mock_create_server.side_effect = [
            Mock(id='test-run-provisioning-server-1'), Mock(id='test-run-provisioning-server-2')
        ]
        mocks.os_server_manager.add_fixture('test-run-provisioning-server-1', 'openstack/api_server_2_active.json')
        mocks.os_server_manager.add_fixture('test-run-provisioning-server-2', 'openstack/api_server_3_active.json')
        mock_reboot1 = mocks.os_server_manager.get_os_server('test-run-provisioning-server-1').reboot
        mock_reboot2 = mocks.os_server_manager.get_os_server('test-run-provisioning-server-2').reboot

        instance = SingleVMOpenEdXInstanceFactory(
            sub_domain='run.provisioning', use_ephemeral_databases=True, attempts=2
        )

        instance.provision()
        self.assertEqual(mocks.mock_set_dns_record.mock_calls, [
            call(name='run.provisioning', type='A', value='192.168.100.200'),
            call(name='studio.run.provisioning', type='CNAME', value='run.provisioning'),
            call(name='run.provisioning', type='A', value='192.168.99.66'),
            call(name='studio.run.provisioning', type='CNAME', value='run.provisioning'),
        ])
        self.assertEqual(mocks.mock_create_server.call_count, 2)  # creates new server for each attempt
        self.assertEqual(mocks.mock_deploy.call_count, 2)
        self.assertEqual(mock_reboot1.call_count, 0)
        self.assertEqual(mock_reboot2.call_count, 1)
        self.assertEqual(mocks.mock_provision_mysql.call_count, 0)
        self.assertEqual(mocks.mock_provision_mongo.call_count, 0)
        self.assertEqual(mocks.mock_provision_swift.call_count, 0)

    @patch_services
    def test_provision_unhandled_exception(self, mocks):
        """
        Make sure that all servers are terminated if there is an unhandled exception during
        provisioning.
        """
        mocks.mock_set_dns_record.side_effect = Exception('Something went catastrophically wrong')
        instance = SingleVMOpenEdXInstanceFactory(sub_domain='run.provisioning')
        with self.assertRaisesRegex(Exception, 'Something went catastrophically wrong'):
            instance.provision()
        self.assertFalse(instance.server_set.exclude_terminated())

        mocks.mock_provision_failed_email.assert_called_once_with(instance.ProvisionMessages.PROVISION_EXCEPTION)

    @patch_services
    def test_provision_with_external_databases(self, mocks):
        """
        Run provisioning sequence, with external databases
        """
        mocks.mock_create_server.side_effect = [Mock(id='test-run-provisioning-server'), None]
        mocks.os_server_manager.add_fixture('test-run-provisioning-server', 'openstack/api_server_2_active.json')

        instance = SingleVMOpenEdXInstanceFactory(sub_domain='run.provisioning', use_ephemeral_databases=False)

        def deploy():
            """
            Make sure that ansible settings are present at deploy time
            """
            ansible_settings = yaml.load(instance.ansible_settings)
            for setting in ('EDXAPP_MYSQL_USER', 'EDXAPP_MONGO_PASSWORD',
                            'EDXAPP_MONGO_USER', 'EDXAPP_MONGO_PASSWORD',
                            'EDXAPP_SWIFT_USERNAME', 'EDXAPP_SWIFT_KEY'):
                self.assertTrue(ansible_settings[setting])
            return (['log'], 0)

        mocks.mock_deploy.side_effect = deploy
        instance.provision()
        self.assertEqual(mocks.mock_provision_mysql.call_count, 1)
        self.assertEqual(mocks.mock_provision_mongo.call_count, 1)
        self.assertEqual(mocks.mock_provision_swift.call_count, 1)
