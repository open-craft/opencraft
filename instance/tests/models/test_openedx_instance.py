# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
OpenEdXInstance model - Tests
"""

# Imports #####################################################################

from datetime import timedelta
from unittest.mock import patch, Mock

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time
import yaml

from instance import gandi
from instance.models.appserver import Status as AppServerStatus
from instance.models.instance import InstanceReference
from instance.models.load_balancer import LoadBalancingServer
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance, OpenEdXAppConfiguration
from instance.models.server import OpenStackServer, Server, Status as ServerStatus
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

@ddt.ddt
class OpenEdXInstanceTestCase(TestCase):
    """
    Test cases for OpenEdXInstance models
    """

    def _assert_defaults(self, instance, name="Instance"):
        """
        Assert that default settings for instance are correct
        """
        self.assertEqual(instance.name, name)
        self.assertEqual(instance.openedx_release, settings.DEFAULT_OPENEDX_RELEASE)
        self.assertEqual(instance.configuration_source_repo_url, settings.DEFAULT_CONFIGURATION_REPO_URL)
        self.assertEqual(instance.configuration_version, settings.DEFAULT_CONFIGURATION_VERSION)
        self.assertEqual(instance.edx_platform_repository_url, settings.DEFAULT_EDX_PLATFORM_REPO_URL)
        self.assertEqual(instance.edx_platform_commit, settings.DEFAULT_OPENEDX_RELEASE)
        self.assertTrue(instance.mysql_server)
        self.assertTrue(instance.mongodb_server)
        self.assertTrue(instance.mysql_user)
        self.assertTrue(instance.mysql_pass)
        self.assertTrue(instance.mongo_user)
        self.assertTrue(instance.mongo_pass)
        self.assertEqual(instance.swift_openstack_user, settings.SWIFT_OPENSTACK_USER)
        self.assertEqual(instance.swift_openstack_password, settings.SWIFT_OPENSTACK_PASSWORD)
        self.assertEqual(instance.swift_openstack_tenant, settings.SWIFT_OPENSTACK_TENANT)
        self.assertEqual(instance.swift_openstack_auth_url, settings.SWIFT_OPENSTACK_AUTH_URL)
        self.assertEqual(instance.swift_openstack_region, settings.SWIFT_OPENSTACK_REGION)
        self.assertEqual(instance.github_admin_organizations, [])
        self.assertEqual(instance.github_admin_users, [])
        self.assertNotEqual(instance.secret_key_b64encoded, '')
        self.assertEqual(instance.openstack_region, settings.OPENSTACK_REGION)
        self.assertEqual(instance.openstack_server_base_image, settings.OPENSTACK_SANDBOX_BASE_IMAGE)
        self.assertEqual(instance.openstack_server_flavor, settings.OPENSTACK_SANDBOX_FLAVOR)
        self.assertEqual(instance.openstack_server_ssh_keyname, settings.OPENSTACK_SANDBOX_SSH_KEYNAME)
        self.assertEqual(instance.created, instance.ref.created)
        self.assertEqual(instance.modified, instance.ref.modified)
        self.assertEqual(instance.additional_security_groups, [])
        self.assertEqual(instance.use_ephemeral_databases, settings.INSTANCE_EPHEMERAL_DATABASES)
        self.assertTrue(instance.rabbitmq_vhost)
        self.assertTrue(instance.rabbitmq_consumer_user)
        self.assertTrue(instance.rabbitmq_provider_user)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=True)
    def test_create_defaults(self):
        """
        Create an instance without specifying additional fields,
        leaving it up to the create method to set them
        """
        instance = OpenEdXInstance.objects.create(sub_domain='sandbox.defaults')
        self._assert_defaults(instance)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=False)
    def test_create_defaults_persistent_databases(self):
        """
        Create an instance without specifying additional fields,
        leaving it up to the create method to set them
        """
        instance = OpenEdXInstance.objects.create(sub_domain='production.defaults')
        self._assert_defaults(instance)

    def test_id_different_from_ref_id(self):
        """
        Check that InstanceReference IDs are always multiples of 10, and OpenEdXInstance IDs
        usually are different from the InstanceReference ID. This is established by the
        migration '0048...', and used to ensure that instance.ref.id is generally used instead
        of instance.id.

        See InstanceReference in instance/models/instance.py for more details.
        """
        instance1 = OpenEdXInstanceFactory()
        instance2 = OpenEdXInstanceFactory()
        self.assertGreaterEqual(instance1.ref.pk, 10)
        self.assertGreaterEqual(instance2.ref.pk, 10)
        self.assertEqual(instance1.ref.pk % 10, 0)
        self.assertEqual(instance2.ref.pk % 10, 0)

        # There is a non-zero chance that instance1.id == instance1.ref.id, though it's highly
        # unlikely. But to be safe, we check two different objects; since the IDs increment
        # at different rates (10 vs 1), this should always be true:
        self.assertTrue(
            (instance1.id != instance1.ref.id) or (instance2.id != instance2.ref.id)
        )

    def test_domain_url(self):
        """
        Domain and URL attributes
        """
        instance = OpenEdXInstanceFactory(
            internal_lms_domain='sample.example.org', name='Sample Instance'
        )
        internal_lms_domain = 'sample.example.org'
        internal_lms_preview_domain = 'preview-sample.example.org'
        internal_studio_domain = 'studio-sample.example.org'
        self.assertEqual(instance.internal_lms_domain, internal_lms_domain)
        self.assertEqual(instance.internal_lms_preview_domain, internal_lms_preview_domain)
        self.assertEqual(instance.internal_studio_domain, internal_studio_domain)
        # External domains are empty by default.
        self.assertEqual(instance.external_lms_domain, '')
        self.assertEqual(instance.external_lms_preview_domain, '')
        self.assertEqual(instance.external_studio_domain, '')
        # When external domain is empty, main domains/URLs equal internal domains.
        self.assertEqual(instance.domain, internal_lms_domain)
        self.assertEqual(instance.lms_preview_domain, internal_lms_preview_domain)
        self.assertEqual(instance.studio_domain, internal_studio_domain)
        self.assertEqual(instance.studio_domain_nginx_regex, r'~^(studio\-sample\.example\.org)$')
        self.assertEqual(instance.url, 'https://{}/'.format(internal_lms_domain))
        self.assertEqual(instance.lms_preview_url, 'https://{}/'.format(internal_lms_preview_domain))
        self.assertEqual(instance.studio_url, 'https://{}/'.format(internal_studio_domain))
        self.assertEqual(str(instance), 'Sample Instance (sample.example.org)')
        # External domains take precedence over internal domains.
        external_lms_domain = 'external.domain.com'
        external_lms_preview_domain = 'lms-preview.external.domain.com'
        external_studio_domain = 'external-studio.domain.com'
        instance.external_lms_domain = external_lms_domain
        instance.external_lms_preview_domain = external_lms_preview_domain
        instance.external_studio_domain = external_studio_domain
        # Internal domains are still the same.
        self.assertEqual(instance.internal_lms_domain, internal_lms_domain)
        self.assertEqual(instance.internal_lms_preview_domain, internal_lms_preview_domain)
        self.assertEqual(instance.internal_studio_domain, internal_studio_domain)
        # Default domains will now equal external domains.
        self.assertEqual(instance.domain, external_lms_domain)
        self.assertEqual(instance.lms_preview_domain, external_lms_preview_domain)
        self.assertEqual(instance.studio_domain, external_studio_domain)
        self.assertEqual(
            instance.studio_domain_nginx_regex,
            r'~^(external\-studio\.domain\.com|studio\-sample\.example\.org)$'
        )
        self.assertEqual(instance.url, 'https://{}/'.format(external_lms_domain))
        self.assertEqual(instance.lms_preview_url, 'https://{}/'.format(external_lms_preview_domain))
        self.assertEqual(instance.studio_url, 'https://{}/'.format(external_studio_domain))
        self.assertEqual(str(instance), 'Sample Instance (external.domain.com)')

    @patch_services
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    def test_spawn_appserver(self, mocks, mock_provision):
        """
        Run spawn_appserver() sequence
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.spawn', use_ephemeral_databases=True)

        appserver_id = instance.spawn_appserver()
        self.assertEqual(mock_provision.call_count, 1)

        self.assertIsNotNone(appserver_id)
        self.assertEqual(instance.appserver_set.count(), 1)
        self.assertFalse(instance.get_active_appservers().exists())

        # We are using ephemeral databases:
        self.assertEqual(mocks.mock_provision_mysql.call_count, 0)
        self.assertEqual(mocks.mock_provision_mongo.call_count, 0)
        self.assertEqual(mocks.mock_provision_swift.call_count, 0)

        lb_domain = instance.load_balancing_server.domain + '.'
        dns_records = gandi.api.client.list_records('example.com')
        self.assertCountEqual(dns_records, [
            dict(name='test.spawn', type='CNAME', value=lb_domain, ttl=1200),
            dict(name='preview-test.spawn', type='CNAME', value=lb_domain, ttl=1200),
            dict(name='studio-test.spawn', type='CNAME', value=lb_domain, ttl=1200),
        ])

        appserver = instance.appserver_set.get(pk=appserver_id)
        self.assertEqual(appserver.name, "AppServer 1")
        self.assertEqual(appserver.instance, instance)
        for field_name in OpenEdXAppConfiguration.get_config_fields():
            self.assertEqual(
                getattr(instance, field_name),
                getattr(appserver, field_name),
            )
        self.assertEqual(appserver.configuration_database_settings, "")
        self.assertEqual(appserver.configuration_storage_settings, "")
        configuration_vars = yaml.load(appserver.configuration_settings)
        self.assertEqual(configuration_vars['COMMON_HOSTNAME'], instance.domain)
        self.assertEqual(configuration_vars['EDXAPP_PLATFORM_NAME'], instance.name)
        self.assertEqual(configuration_vars['EDXAPP_CONTACT_EMAIL'], instance.email)

    @override_settings(NEWRELIC_LICENSE_KEY='newrelic-key')
    @patch_services
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    def test_newrelic_configuration(self, mocks, mock_provision):
        """
        Check that newrelic ansible vars are set correctly
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.newrelic', use_ephemeral_databases=True)
        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        configuration_vars = yaml.load(appserver.configuration_settings)
        self.assertIs(configuration_vars['COMMON_ENABLE_NEWRELIC'], True)
        self.assertIs(configuration_vars['COMMON_ENABLE_NEWRELIC_APP'], True)
        self.assertEqual(configuration_vars['COMMON_ENVIRONMENT'], 'opencraft')
        self.assertEqual(configuration_vars['COMMON_DEPLOYMENT'], instance.internal_lms_domain)
        self.assertEqual(configuration_vars['NEWRELIC_LICENSE_KEY'], 'newrelic-key')

    @patch_services
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    def test_spawn_appserver_with_external_domains(self, mocks, mock_provision):
        """
        Test that relevant configuration variables use external domains when provisioning a new app server.
        """
        instance = OpenEdXInstanceFactory(
            sub_domain='test.spawn',
            use_ephemeral_databases=True,
            external_lms_domain='lms.external.com',
            external_lms_preview_domain='lmspreview.external.com',
            external_studio_domain='cms.external.com'
        )

        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        configuration_vars = yaml.load(appserver.configuration_settings)
        self.assertEqual(configuration_vars['COMMON_HOSTNAME'], instance.external_lms_domain)
        self.assertEqual(configuration_vars['EDXAPP_LMS_BASE'], instance.external_lms_domain)
        self.assertEqual(configuration_vars['EDXAPP_PREVIEW_LMS_BASE'], instance.external_lms_preview_domain)
        self.assertEqual(configuration_vars['EDXAPP_CMS_BASE'], instance.external_studio_domain)

    @patch_services
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    def test_spawn_appserver_names(self, mocks, mock_provision):
        """
        Run spawn_appserver() sequence multiple times and check names of resulting app servers
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.spawn_names', use_ephemeral_databases=True)

        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        self.assertEqual(appserver.name, "AppServer 1")

        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        self.assertEqual(appserver.name, "AppServer 2")

        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        self.assertEqual(appserver.name, "AppServer 3")

    @patch_services
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    def test_spawn_appserver_with_lms_users(self, mocks, mock_provision):
        """
        Provision an AppServer with a user added to lms_users.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.spawn', use_ephemeral_databases=True)
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        instance.lms_users.add(user)
        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        self.assertEqual(appserver.lms_users.count(), 1)
        self.assertEqual(appserver.lms_users.get(), user)
        self.assertTrue(appserver.lms_user_settings)

    @patch_services
    def test_spawn_appserver_detailed(self, mocks):
        """
        Test spawning an AppServer in more detail; this is partially an integration test

        Unlike test_spawn_appserver(), this test does not mock the .provision() method, so the
        AppServer will go through the motions of provisioning and end up with the appropriate
        status.

        Note that OpenEdXInstance does not include auto-retry support or auto-activation upon
        success; those behaviors are implemented at the task level in tasks.py and tested in
        test_tasks.py
        """
        mocks.mock_create_server.side_effect = [Mock(id='test-run-provisioning-server'), None]
        mocks.os_server_manager.add_fixture('test-run-provisioning-server', 'openstack/api_server_2_active.json')

        instance = OpenEdXInstanceFactory(
            sub_domain='test.spawn',
            use_ephemeral_databases=True,
        )
        self.assertEqual(instance.appserver_set.count(), 0)
        self.assertFalse(instance.get_active_appservers().exists())
        appserver_id = instance.spawn_appserver()
        self.assertIsNotNone(appserver_id)
        self.assertEqual(instance.appserver_set.count(), 1)
        self.assertFalse(instance.get_active_appservers().exists())

        appserver = instance.appserver_set.get(pk=appserver_id)
        self.assertFalse(appserver.is_active)
        self.assertEqual(appserver.status, AppServerStatus.Running)
        self.assertEqual(appserver.server.status, Server.Status.Ready)

    @patch_services
    def test_spawn_appserver_failed(self, mocks):
        """
        Test what happens when unable to completely spawn an AppServer.
        """
        mocks.mock_run_ansible_playbooks.return_value = (['log: provisioning failed'], 1)
        mocks.mock_create_server.side_effect = [Mock(id='test-run-provisioning-server'), None]
        mocks.os_server_manager.add_fixture('test-run-provisioning-server', 'openstack/api_server_2_active.json')

        instance = OpenEdXInstanceFactory(sub_domain='test.spawn', use_ephemeral_databases=True)
        self.assertEqual(instance.appserver_set.count(), 0)
        self.assertFalse(instance.get_active_appservers().exists())
        result = instance.spawn_appserver()
        self.assertIsNone(result)
        self.assertFalse(instance.get_active_appservers().exists())

        # however, an AppServer will still have been created:
        self.assertEqual(instance.appserver_set.count(), 1)
        appserver = instance.appserver_set.last()
        self.assertEqual(appserver.status, AppServerStatus.ConfigurationFailed)

    @patch_services
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    def test_spawn_appserver_with_external_databases(self, mocks, mock_provision):
        """
        Run spawn_appserver() sequence, with external databases
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.persistent', use_ephemeral_databases=False)

        appserver_id = instance.spawn_appserver()
        self.assertEqual(mocks.mock_provision_mysql.call_count, 1)
        self.assertEqual(mocks.mock_provision_mongo.call_count, 1)
        self.assertEqual(mocks.mock_provision_swift.call_count, 1)

        appserver = instance.appserver_set.get(pk=appserver_id)
        ansible_vars = yaml.load(appserver.configuration_settings)
        for setting in ('EDXAPP_MYSQL_USER', 'EDXAPP_MONGO_PASSWORD',
                        'EDXAPP_MONGO_USER', 'EDXAPP_MONGO_PASSWORD',
                        'EDXAPP_SWIFT_USERNAME', 'EDXAPP_SWIFT_KEY'):
            self.assertTrue(ansible_vars[setting])

    @patch_services
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.provision', return_value=True)
    def test_forum_api_key(self, mocks, mock_provision):
        """
        Ensure the FORUM_API_KEY matches EDXAPP_COMMENTS_SERVICE_KEY
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.forum_api_key', use_ephemeral_databases=True)
        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        configuration_vars = yaml.load(appserver.configuration_settings)
        api_key = configuration_vars['EDXAPP_COMMENTS_SERVICE_KEY']
        self.assertIsNot(api_key, '')
        self.assertIsNotNone(api_key)
        self.assertEqual(configuration_vars['FORUM_API_KEY'], api_key)

    def _check_load_balancer_configuration(self, backend_map, config, domain_names, ip_address):
        """
        Verify the load balancer configuration given in backend_map and config.
        """
        [(backend, config_str)] = config
        self.assertRegex(config_str, r"\bserver\b.*\b{}:80\b".format(ip_address))
        self.assertCountEqual(backend_map, [(domain, backend) for domain in domain_names])

    @patch_services
    def test_get_load_balancer_configuration(self, mocks):
        """
        Test that the load balancer configuration gets generated correctly.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.load_balancer', use_ephemeral_databases=True)
        domain_names = [
            "test.load_balancer.example.com",
            "preview-test.load_balancer.example.com",
            "studio-test.load_balancer.example.com",
        ]

        # Test configuration for preliminary page
        backend_map, config = instance.get_load_balancer_configuration()
        self._check_load_balancer_configuration(
            backend_map, config, domain_names, settings.PRELIMINARY_PAGE_SERVER_IP
        )

        # Test configuration for active appserver
        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        appserver.make_active()
        backend_map, config = instance.get_load_balancer_configuration()
        self._check_load_balancer_configuration(
            backend_map, config, domain_names, appserver.server.public_ip,
        )

        # Test configuration in case an active appserver doesn't have a public IP address anymore.
        # This might happen if the OpenStack server dies or gets modified from the outside, but it
        # is not expected to happen under normal circumstances.  We deconfigure the backend and log
        # an error in this case.
        with patch('instance.openstack_utils.get_server_public_address', return_value=None), \
                self.assertLogs("instance.models.instance", "ERROR"):
            self.assertEqual(instance.get_load_balancer_configuration(), ([], []))

    def test_get_load_balancer_config_ext_domains(self):
        """
        Test the load balancer configuration when external domains are set.
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.load_balancer.opencraft.hosting',
                                          external_lms_domain='courses.myexternal.org',
                                          external_lms_preview_domain='preview.myexternal.org',
                                          external_studio_domain='studio.myexternal.org',
                                          use_ephemeral_databases=True)
        domain_names = [
            'test.load_balancer.opencraft.hosting',
            'preview-test.load_balancer.opencraft.hosting',
            'studio-test.load_balancer.opencraft.hosting',
            'courses.myexternal.org',
            'preview.myexternal.org',
            'studio.myexternal.org',
        ]
        backend_map, config = instance.get_load_balancer_configuration()
        self._check_load_balancer_configuration(
            backend_map, config, domain_names, settings.PRELIMINARY_PAGE_SERVER_IP
        )

    @ddt.data(True, False)
    @patch_services
    @patch('instance.models.openedx_instance.OpenEdXInstance.archive')
    @patch('instance.models.mixins.database.MySQLInstanceMixin.deprovision_mysql')
    @patch('instance.models.mixins.database.MongoDBInstanceMixin.deprovision_mongo')
    @patch('instance.models.mixins.storage.SwiftContainerInstanceMixin.deprovision_swift')
    def test_delete_instance(self, mocks, delete_by_ref, *mock_methods):
        """
        Test that an instance can be deleted directly or by its InstanceReference.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.deletion', use_ephemeral_databases=True)
        instance_ref = instance.ref
        appserver = OpenEdXAppServer.objects.get(pk=instance.spawn_appserver())

        for method in mock_methods:
            self.assertEqual(
                method.call_count, 0,
                '{} should not have been called'.format(method._mock_name)
            )

        # Now delete the instance, either using InstanceReference or the OpenEdXInstance class:
        if delete_by_ref:
            instance_ref.delete()
        else:
            instance.delete()

        for method in mock_methods:
            self.assertEqual(
                method.call_count, 1,
                '{} should have been called exactly once'.format(method._mock_name)
            )

        with self.assertRaises(OpenEdXInstance.DoesNotExist):
            OpenEdXInstance.objects.get(pk=instance.pk)
        with self.assertRaises(InstanceReference.DoesNotExist):
            instance_ref.refresh_from_db()
        with self.assertRaises(OpenEdXAppServer.DoesNotExist):
            appserver.refresh_from_db()

    @staticmethod
    def _set_appserver_terminated(appserver):
        """
        Transition `appserver` to AppServerStatus.Terminated.
        """
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_running()
        appserver._status_to_terminated()

    @staticmethod
    def _set_appserver_running(appserver):
        """
        Transition `appserver` to AppServerStatus.Running.
        """
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_running()

    @staticmethod
    def _set_appserver_configuration_failed(appserver):
        """
        Transition `appserver` to AppServerStatus.ConfigurationFailed.
        """
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_configuration_failed()

    @staticmethod
    def _set_appserver_errored(appserver):
        """
        Transition `appserver` to AppServerStatus.Error.
        """
        appserver._status_to_waiting_for_server()
        appserver._status_to_error()

    @staticmethod
    def _set_server_ready(server):
        """
        Transition `server` to Status.Ready.
        """
        server._status_to_building()
        server._status_to_booting()
        server._status_to_ready()

    @staticmethod
    def _set_server_terminated(server):
        """
        Transition `server` to Status.Terminated.

        Note that servers are allowed to transition to ServerStatus.Terminated from any state,
        so it is not necessary to transition to another status first.
        """
        server._status_to_terminated()

    def _create_appserver(self, instance, status):
        """
        Return appserver for `instance` that has `status`

        Note that this method does not set the status of the VM (OpenStackServer)
        that is associated with the app server.

        Client code is expected to take care of that itself (if necessary).
        """
        appserver = make_test_appserver(instance)
        if status == AppServerStatus.Running:
            self._set_appserver_running(appserver)
        if status == AppServerStatus.ConfigurationFailed:
            self._set_appserver_configuration_failed(appserver)
        elif status == AppServerStatus.Error:
            self._set_appserver_errored(appserver)
        elif status == AppServerStatus.Terminated:
            self._set_appserver_terminated(appserver)
        return appserver

    def _create_running_appserver(self, instance):
        """
        Return app server for `instance` that has `status` AppServerStatus.Running
        """
        return self._create_appserver(instance, AppServerStatus.Running)

    def _create_failed_appserver(self, instance, with_running_server=False):
        """
        Return app server for `instance` that has `status` AppServerStatus.ConfigurationFailed
        """
        return self._create_appserver(instance, AppServerStatus.ConfigurationFailed)

    def _create_errored_appserver(self, instance):
        """
        Return app server for `instance` that has `status` AppServerStatus.Error
        """
        return self._create_appserver(instance, AppServerStatus.Error)

    def _create_terminated_appserver(self, instance):
        """
        Return app server for `instance` that has `status` AppServerStatus.Terminated
        """
        return self._create_appserver(instance, AppServerStatus.Terminated)

    def _assert_status(self, appservers):
        """
        Assert that status of app servers in `appservers` matches expected status.

        Assumes that `appservers` is an iterable of tuples of the following form:

            (<appserver>, <expected status>, <expected server status>)

        where <expected status> is the expected AppServerStatus of <appserver>,
        and <expected server status> is the expected ServerStatus of the OpenStackServer associated with <appserver>.
        """
        for appserver, expected_status, expected_server_status in appservers:
            appserver.refresh_from_db()
            self.assertEqual(appserver.status, expected_status)
            # Status of appserver.server is still stale after refresh_from_db, so reload server manually:
            server = OpenStackServer.objects.get(id=appserver.server.pk)
            self.assertEqual(server.status, expected_server_status)

    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    def test_archive(self, mock_reconfigure, mock_disable_monitoring, mock_remove_dns_records):
        """
        Test that `archive` method terminates all app servers belonging to an instance
        and disables monitoring.
        """
        instance = OpenEdXInstanceFactory()
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        reference_date = timezone.now()

        # Create app servers
        with freeze_time(reference_date - timedelta(days=5)):
            obsolete_appserver = self._create_running_appserver(instance)
            obsolete_appserver_failed = self._create_failed_appserver(instance)

        with freeze_time(reference_date - timedelta(days=1)):
            recent_appserver = self._create_running_appserver(instance)
            recent_appserver_failed = self._create_failed_appserver(instance)

        with freeze_time(reference_date):
            active_appserver = self._create_running_appserver(instance)

        with freeze_time(reference_date + timedelta(days=3)):
            newer_appserver = self._create_running_appserver(instance)
            newer_appserver_failed = self._create_failed_appserver(instance)

        # Set single app server active
        active_appserver.make_active()
        active_appserver.refresh_from_db()

        self.assertEqual(mock_reconfigure.call_count, 1)
        self.assertEqual(mock_disable_monitoring.call_count, 0)
        self.assertEqual(mock_remove_dns_records.call_count, 0)

        # Instance should not be marked as archived
        self.assertFalse(instance.ref.is_archived)

        # Shut down instance
        instance.archive()

        # Now the instance should be marked as archived
        self.assertTrue(instance.ref.is_archived)

        self.assertEqual(mock_reconfigure.call_count, 2)
        self.assertEqual(mock_disable_monitoring.call_count, 1)
        self.assertEqual(mock_remove_dns_records.call_count, 1)

        # Check status of running app servers
        self._assert_status([
            (obsolete_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (recent_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (active_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (newer_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
        ])

        # Check status of failed app servers:
        # AppServerStatus.Terminated is reserved for instances that were running successfully at some point,
        # so app servers with AppServerStatus.ConfigurationFailed will still have that status
        # after `shut_down` calls `terminate_vm` on them.
        # However, the VM (OpenStackServer) that an app server is associated with
        # *should* have ServerStatus.Terminated if the app server was old enough to be terminated.
        self._assert_status([
            (obsolete_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (recent_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (newer_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
        ])

    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    def test_archive_no_active_appserver(self, mock_reconfigure, mock_disable_monitoring, mock_remove_dns_records):
        """
        Test that the archive method works correctly if no appserver is active.
        """
        instance = OpenEdXInstanceFactory()
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        appserver = self._create_running_appserver(instance)
        instance.archive()
        self.assertEqual(mock_reconfigure.call_count, 1)
        self.assertEqual(mock_disable_monitoring.call_count, 1)
        self.assertEqual(mock_remove_dns_records.call_count, 1)
        self._assert_status([
            (appserver, AppServerStatus.Terminated, ServerStatus.Terminated)
        ])
        self.assertTrue(instance.ref.is_archived)

    @ddt.data(2, 5, 10)
    @patch_services
    def test_terminate_obsolete_appservers(self, mock_services, days):
        """
        When there is an active appserver, test that `terminate_obsolete_appservers`
        correctly identifies and terminates app servers created more than `days` before now, except:
        - the active appserver
        - a release candidate server (the most recent running appserver)
        - a fallback appserver for `days` after activation (the most recent running appserver created
          before the currently-active app server was activated)
        """
        instance = OpenEdXInstanceFactory()
        reference_date = timezone.now()

        # Create app servers
        with freeze_time(reference_date - timedelta(days=days + 3)):
            oldest_appserver = self._create_running_appserver(instance)
            oldest_appserver_failed = self._create_failed_appserver(instance)

        with freeze_time(reference_date - timedelta(days=days + 2)):
            fallback_appserver = self._create_running_appserver(instance)
            fallback_appserver_failed = self._create_failed_appserver(instance)

        with freeze_time(reference_date - timedelta(days=1)):
            active_appserver = self._create_running_appserver(instance)

        with freeze_time(reference_date + timedelta(days=days + 2)):
            rc_appserver = self._create_running_appserver(instance)
            rc_appserver_failed = self._create_failed_appserver(instance)

        # Set single app server active - this will be the reference date
        with freeze_time(reference_date):
            active_appserver.make_active()

        # Terminate app servers - only the oldest and failed fallback appservers should be terminated,
        # as all the other appservers were either created less than `days` before now,
        # or kept as a fallback appserver
        with freeze_time(reference_date):
            instance.terminate_obsolete_appservers(days=days)

        # Check status of running app servers
        self._assert_status([
            (oldest_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (fallback_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (active_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (rc_appserver, AppServerStatus.Running, ServerStatus.Pending),
        ])

        # Check status of failed app servers:
        # AppServerStatus.Terminated is reserved for instances that were running successfully at some point,
        # so app servers with AppServerStatus.ConfigurationFailed will still have that status
        # after `terminate_obsolete_appservers` calls `terminate_vm` on them.
        # However, the VM (OpenStackServer) that an app server is associated with
        # *should* have ServerStatus.Terminated if the app server was old enough to be terminated.
        self._assert_status([
            (oldest_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (fallback_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (rc_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
        ])

        # Terminate app servers after `days` have passed - the fallback appserver should be terminated
        # but the other appservers still running should be preserved
        with freeze_time(reference_date + timedelta(days=days + 1)):
            instance.terminate_obsolete_appservers(days=days)

        self._assert_status([
            (oldest_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (oldest_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (fallback_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (fallback_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (active_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (rc_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (rc_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
        ])

        # Terminate app servers again, much later - this time only the active appserver and the most recent
        # running appserver should remain
        with freeze_time(reference_date + timedelta(days=days * 3)):
            instance.terminate_obsolete_appservers(days=days)

        self._assert_status([
            (oldest_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (oldest_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (fallback_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (fallback_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (active_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (rc_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (rc_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
        ])

    @ddt.data(2, 5, 10)
    @patch_services
    def test_terminate_obsolete_appservers_no_active(self, mock_services, days):
        """
        When there is NO active appserver, test that `terminate_obsolete_appservers`
        correctly identifies and terminates app servers created more than `days` before now,
        except a release candidate server (the most recent running appserver)
        """
        instance = OpenEdXInstanceFactory()
        reference_date = timezone.now()

        # Create app servers
        with freeze_time(reference_date - timedelta(days=days + 1)):
            oldest_appserver = self._create_running_appserver(instance)
            oldest_appserver_failed = self._create_failed_appserver(instance)

        with freeze_time(reference_date - timedelta(days=days - 1)):
            recent_appserver = self._create_running_appserver(instance)
            recent_appserver_failed = self._create_failed_appserver(instance)

        with freeze_time(reference_date + timedelta(days=days)):
            rc_appserver = self._create_running_appserver(instance)
            rc_appserver_failed = self._create_failed_appserver(instance)

        # Terminate app servers - recent appservers aren't older than `days` yet
        with freeze_time(reference_date):
            instance.terminate_obsolete_appservers(days=days)

        # Check status of app servers - only the oldest appservers should be terminated
        self._assert_status([
            (oldest_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (oldest_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (recent_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (recent_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (rc_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (rc_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
        ])

        # Terminate app servers - now all appservers are older than `days`, but the rc should still be kept
        with freeze_time(reference_date + timedelta(days=days * 2 + 1)):
            instance.terminate_obsolete_appservers()

        # Check status of app servers - only the oldest and recent appservers should now be terminated
        self._assert_status([
            (oldest_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (oldest_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (recent_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (recent_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (rc_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (rc_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
        ])

    def test_shut_down_reminder(self):
        """
        Test that if developers run the shut_down() method on the console, they see a warning
        """
        instance = OpenEdXInstanceFactory()
        msg = r"Use archive\(\) to shut down all of an instances app servers and remove it from the instance list."
        with self.assertRaisesRegex(AttributeError, msg):
            instance.shut_down()
