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

import codecs
from datetime import timedelta
from unittest.mock import call, patch, Mock
from uuid import uuid4
import re

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
import requests
import responses
import yaml
import six

from instance import gandi
from instance import newrelic
from instance.models.appserver import Status as AppServerStatus
from instance.models.instance import InstanceReference
from instance.models.load_balancer import LoadBalancingServer
from instance.models.mixins.secret_keys import OPENEDX_SECRET_KEYS, OPENEDX_SHARED_KEYS
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance, OpenEdXAppConfiguration
from instance.models.openedx_appserver import DEFAULT_EDX_PLATFORM_REPO_URL
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
    # pylint: disable=too-many-public-methods
    def _assert_defaults(self, instance, name="Instance"):
        """
        Assert that default settings for instance are correct
        """
        self.assertEqual(instance.name, name)
        self.assertEqual(instance.openedx_release, settings.DEFAULT_OPENEDX_RELEASE)
        self.assertEqual(instance.configuration_source_repo_url, settings.DEFAULT_CONFIGURATION_REPO_URL)
        self.assertEqual(instance.configuration_version, settings.DEFAULT_CONFIGURATION_VERSION)
        self.assertEqual(instance.edx_platform_repository_url, DEFAULT_EDX_PLATFORM_REPO_URL)
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

    def test_update_defaults(self):
        """
        Check that database and storage settings don't change when updating an instance's settings.

        Since 'set_field_defaults' is currently only called if an instance has not been saved to the database,
        the chances of it overriding existing values are non-existent.

        But we include this test anyway to guard against regressions.
        """
        instance = OpenEdXInstance.objects.create(sub_domain='testing.defaults')
        self._assert_defaults(instance)

        mysql_server = instance.mysql_server
        mongodb_server = instance.mongodb_server
        mysql_user = instance.mysql_user
        mysql_pass = instance.mysql_pass
        mongo_user = instance.mongo_user
        mongo_pass = instance.mongo_pass
        secret_key = instance.secret_key_b64encoded

        instance.name = "Test Instance"
        instance.save()
        instance.refresh_from_db()
        self._assert_defaults(instance, name=instance.name)

        self.assertEqual(instance.mysql_server.pk, mysql_server.pk)
        self.assertEqual(instance.mongodb_server.pk, mongodb_server.pk)
        self.assertEqual(instance.mysql_user, mysql_user)
        self.assertEqual(instance.mysql_pass, mysql_pass)
        self.assertEqual(instance.mongo_user, mongo_user)
        self.assertEqual(instance.mongo_pass, mongo_pass)
        self.assertEqual(instance.secret_key_b64encoded, secret_key)

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
        self.assertEqual(instance.url, 'http://{}/'.format(internal_lms_domain))
        self.assertEqual(instance.lms_preview_url, 'http://{}/'.format(internal_lms_preview_domain))
        self.assertEqual(instance.studio_url, 'http://{}/'.format(internal_studio_domain))
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
        self.assertEqual(instance.url, 'http://{}/'.format(external_lms_domain))
        self.assertEqual(instance.lms_preview_url, 'http://{}/'.format(external_lms_preview_domain))
        self.assertEqual(instance.studio_url, 'http://{}/'.format(external_studio_domain))
        self.assertEqual(str(instance), 'Sample Instance (external.domain.com)')
        # URLs respect the protocol setting.
        instance.protocol = 'https'
        self.assertEqual(instance.url, 'https://{}/'.format(external_lms_domain))
        self.assertEqual(instance.lms_preview_url, 'https://{}/'.format(external_lms_preview_domain))
        self.assertEqual(instance.studio_url, 'https://{}/'.format(external_studio_domain))

    @patch_services
    @patch('instance.models.openedx_instance.OpenEdXAppServer.provision', return_value=True)
    def test_spawn_appserver(self, mocks, mock_provision):
        """
        Run spawn_appserver() sequence
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.spawn', use_ephemeral_databases=True)

        appserver_id = instance.spawn_appserver()
        self.assertEqual(mock_provision.call_count, 1)

        self.assertIsNotNone(appserver_id)
        self.assertEqual(instance.appserver_set.count(), 1)
        self.assertIsNone(instance.active_appserver)

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
    @patch('instance.models.openedx_instance.OpenEdXAppServer.provision', return_value=True)
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
    @patch('instance.models.openedx_instance.OpenEdXAppServer.provision', return_value=True)
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
    def test_set_appserver_active(self, mocks):
        """
        Test set_appserver_active() and set_appserver_inactive()
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.opencraft.co.uk',
                                          use_ephemeral_databases=True)
        appserver_id = instance.spawn_appserver()
        instance.set_appserver_active(appserver_id)
        instance.refresh_from_db()
        self.assertEqual(instance.active_appserver.pk, appserver_id)
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 2)
        self.assertEqual(mocks.mock_enable_monitoring.call_count, 1)
        instance.set_appserver_inactive()
        instance.refresh_from_db()
        self.assertIsNone(instance.active_appserver)
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 3)
        self.assertEqual(mocks.mock_disable_monitoring.call_count, 0)

    @patch_services
    @patch('instance.models.openedx_instance.OpenEdXAppServer.provision', return_value=True)
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
    @patch('instance.models.openedx_instance.OpenEdXAppServer.provision', return_value=True)
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
        self.assertIsNone(instance.active_appserver)
        appserver_id = instance.spawn_appserver()
        self.assertIsNotNone(appserver_id)
        self.assertEqual(instance.appserver_set.count(), 1)
        self.assertIsNone(instance.active_appserver)

        appserver = instance.appserver_set.get(pk=appserver_id)
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
        self.assertIsNone(instance.active_appserver)
        result = instance.spawn_appserver()
        self.assertIsNone(result)
        self.assertIsNone(instance.active_appserver)

        # however, an AppServer will still have been created:
        self.assertEqual(instance.appserver_set.count(), 1)
        appserver = instance.appserver_set.last()
        self.assertEqual(appserver.status, AppServerStatus.ConfigurationFailed)

    @patch_services
    @patch('instance.models.openedx_instance.OpenEdXAppServer.provision', return_value=True)
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
    @patch('instance.models.openedx_instance.OpenEdXAppServer.provision', return_value=True)
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
        instance.set_appserver_active(appserver_id)
        backend_map, config = instance.get_load_balancer_configuration()
        self._check_load_balancer_configuration(
            backend_map, config, domain_names, instance.active_appserver.server.public_ip
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
    @patch('instance.models.openedx_instance.OpenEdXInstance.shut_down')
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

    def _create_appserver(self, instance, status, created=None):
        """
        Return appserver for `instance` that has `status`, and (optionally) was `created` on a specific date.

        Note that this method does not set the status of the VM (OpenStackServer)
        that is associated with the app server.

        Client code is expected to take care of that itself (if necessary).
        """
        appserver = make_test_appserver(instance)
        if created:
            appserver.created = created
            appserver.save()
        if status == AppServerStatus.Running:
            self._set_appserver_running(appserver)
        if status == AppServerStatus.ConfigurationFailed:
            self._set_appserver_configuration_failed(appserver)
        elif status == AppServerStatus.Error:
            self._set_appserver_errored(appserver)
        elif status == AppServerStatus.Terminated:
            self._set_appserver_terminated(appserver)
        return appserver

    def _create_running_appserver(self, instance, created=None):
        """
        Return app server for `instance` that has `status` AppServerStatus.Running,
        and (optionally) was `created` on a specific date.
        """
        return self._create_appserver(instance, AppServerStatus.Running, created)

    def _create_failed_appserver(self, instance, created=None, with_running_server=False):
        """
        Return app server for `instance` that has `status` AppServerStatus.ConfigurationFailed,
        and (optionally) was `created` on a specific date.
        """
        return self._create_appserver(instance, AppServerStatus.ConfigurationFailed, created)

    def _create_errored_appserver(self, instance, created=None):
        """
        Return app server for `instance` that has `status` AppServerStatus.Error,
        and (optionally) was `created` on a specific date.
        """
        return self._create_appserver(instance, AppServerStatus.Error, created)

    def _create_terminated_appserver(self, instance, created=None):
        """
        Return app server for `instance` that has `status` AppServerStatus.Terminated,
        and (optionally) was `created` on a specific date.
        """
        return self._create_appserver(instance, AppServerStatus.Terminated, created)

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

    @ddt.data(
        # No app servers; monitoring disabled
        (0, 0, 0, False, False),
        # No app servers; monitoring enabled
        (0, 0, 0, True, False),
        # No running, no terminated, and some failed app servers with VM ready; monitoring disabled
        (0, 0, 3, False, False),
        # No running, no terminated, and some failed app servers with VM ready; monitoring enabled
        (0, 0, 3, True, False),
        # No running, some terminated, and no failed app servers with VM ready; monitoring disabled
        (0, 3, 0, False, True),
        # No running, some terminated, and no failed app servers with VM ready; monitoring enabled
        (0, 3, 0, True, False),
        # No running, some terminated, and some failed app servers with VM ready; monitoring disabled
        (0, 3, 3, False, False),
        # No running, some terminated, and some failed app servers with VM ready; monitoring enabled
        (0, 3, 3, True, False),
        # Some running, no terminated, and no failed app servers with VM ready; monitoring disabled
        (3, 0, 0, False, False),
        # Some running, no terminated, and no failed app servers with VM ready; monitoring enabled
        (3, 0, 0, True, False),
        # Some running, some terminated, and no failed app servers with VM ready; monitoring disabled
        (3, 3, 0, False, False),
        # Some running, some terminated, and no failed app servers with VM ready; monitoring enabled
        (3, 3, 0, True, False),
        # Some running, no terminated, and some failed app servers with VM ready; monitoring disabled
        (3, 0, 3, False, False),
        # Some running, no terminated, and some failed app servers with VM ready; monitoring enabled
        (3, 0, 3, True, False),
        # Some running, some terminated, and some failed app servers with VM ready; monitoring disabled
        (3, 3, 3, False, False),
        # Some running, some terminated, and some failed app servers with VM ready; monitoring enabled
        (3, 3, 3, True, False),
    )
    @ddt.unpack
    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_is_shut_down(
            self,
            num_running_appservers,
            num_terminated_appservers,
            num_failed_appservers_vm_ready,
            monitoring_enabled,
            expected_result,
            mock_newrelic
    ):
        """
        Test that `is_shut_down` property correctly reports whether an instance has been shut down.

        An instance has been shut down if monitoring has been turned off
        and each of its app servers has either been terminated
        or failed to provision and the corresponding VM has since been terminated.

        If an instance has no app servers, we assume that it has *not* been shut down.
        This ensures that the GUI lists newly created instances without app servers.
        """
        instance = OpenEdXInstanceFactory()

        for dummy in range(num_running_appservers):
            self._create_running_appserver(instance)
        for dummy in range(num_terminated_appservers):
            self._create_terminated_appserver(instance)
        failed_appservers = [
            self._create_failed_appserver(instance) for dummy in range(num_terminated_appservers)
        ]
        errored_appservers = [
            self._create_errored_appserver(instance) for dummy in range(num_terminated_appservers)
        ]
        for failed_appserver in failed_appservers + errored_appservers:
            self._set_server_terminated(failed_appserver.server)

        if num_failed_appservers_vm_ready:
            failed_appservers_vm_ready = [
                self._create_failed_appserver(instance) for dummy in range(num_terminated_appservers)
            ]
            for failed_appserver in failed_appservers_vm_ready:
                self._set_server_ready(failed_appserver.server)

        if monitoring_enabled:
            monitor_id = str(uuid4())
            instance.new_relic_availability_monitors.create(pk=monitor_id)

        self.assertEqual(instance.is_shut_down, expected_result)

    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    def test_shut_down(self, mock_reconfigure, mock_disable_monitoring, mock_remove_dns_records):
        """
        Test that `shut_down` method terminates all app servers belonging to an instance
        and disables monitoring.
        """
        instance = OpenEdXInstanceFactory()
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        reference_date = timezone.now()

        # Create app servers
        obsolete_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=5))
        obsolete_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=5))

        recent_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=1))
        recent_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=1))

        active_appserver = self._create_running_appserver(instance, reference_date)

        newer_appserver = self._create_running_appserver(instance, reference_date + timedelta(days=3))
        newer_appserver_failed = self._create_failed_appserver(instance, reference_date + timedelta(days=3))

        # Set single app server active
        instance.active_appserver = active_appserver
        instance.save()
        active_appserver.instance.refresh_from_db()

        self.assertEqual(mock_reconfigure.call_count, 0)
        self.assertEqual(mock_disable_monitoring.call_count, 0)
        self.assertEqual(mock_remove_dns_records.call_count, 0)

        # Shut down instance
        instance.shut_down()

        self.assertEqual(mock_reconfigure.call_count, 1)
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
    def test_shut_down_no_active_appserver(self, mock_reconfigure, mock_disable_monitoring, mock_remove_dns_records):
        """
        Test that the shut_down method works correctly if no appserver is active.
        """
        instance = OpenEdXInstanceFactory()
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
        appserver = self._create_running_appserver(instance)
        instance.shut_down()
        self.assertEqual(mock_reconfigure.call_count, 1)
        self.assertEqual(mock_disable_monitoring.call_count, 1)
        self.assertEqual(mock_remove_dns_records.call_count, 1)
        self._assert_status([
            (appserver, AppServerStatus.Terminated, ServerStatus.Terminated)
        ])

    @patch('instance.models.mixins.load_balanced.LoadBalancedInstance.remove_dns_records')
    @patch('instance.models.load_balancer.LoadBalancingServer.reconfigure')
    @responses.activate
    def test_shut_down_monitors_not_found(self, *mock_methods):
        """
        Test that instance `is_shut_down` after calling `shut_down` on it,
        even if monitors associated with it no longer exist.
        """
        monitor_ids = [str(uuid4()) for i in range(3)]
        instance = OpenEdXInstanceFactory()
        appserver = self._create_running_appserver(instance)
        instance.active_appserver = appserver
        instance.save()
        appserver.instance.refresh_from_db()

        for monitor_id in monitor_ids:
            instance.new_relic_availability_monitors.create(pk=monitor_id)
            responses.add(
                responses.DELETE,
                '{0}/monitors/{1}'.format(newrelic.SYNTHETICS_API_URL, monitor_id),
                status=requests.codes.not_found  # pylint: disable=no-member
            )

        # Preconditions
        self.assertEqual(instance.new_relic_availability_monitors.count(), 3)
        self.assertFalse(instance.is_shut_down)

        # Shut down instance
        instance.shut_down()

        # Instance should
        # - no longer have any monitors associated with it
        # - no longer have any running app servers
        # - be considered "shut down"
        self.assertEqual(instance.new_relic_availability_monitors.count(), 0)
        self._assert_status([
            (appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
        ])
        self.assertTrue(instance.is_shut_down)

    @ddt.data(2, 5, 10)
    def test_terminate_obsolete_appservers(self, days):
        """
        Test that `terminate_obsolete_appservers` correctly identifies and terminates app servers
        that were created (more than) `days` before the currently-active app server of the parent instance.
        """
        instance = OpenEdXInstanceFactory()
        reference_date = timezone.now()

        # Create app servers
        obsolete_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=days + 1))
        obsolete_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=days + 1))

        recent_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=days - 1))
        recent_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=days - 1))

        active_appserver = self._create_running_appserver(instance, reference_date)

        newer_appserver = self._create_running_appserver(instance, reference_date + timedelta(days=days))
        newer_appserver_failed = self._create_failed_appserver(instance, reference_date + timedelta(days=days))

        # Set single app server active
        instance.active_appserver = active_appserver
        instance.save()

        # Terminate app servers
        instance.terminate_obsolete_appservers(days=days)

        # Check status of running app servers
        self._assert_status([
            (obsolete_appserver, AppServerStatus.Terminated, ServerStatus.Terminated),
            (recent_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (active_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (newer_appserver, AppServerStatus.Running, ServerStatus.Pending),
        ])

        # Check status of failed app servers:
        # AppServerStatus.Terminated is reserved for instances that were running successfully at some point,
        # so app servers with AppServerStatus.ConfigurationFailed will still have that status
        # after `terminate_obsolete_appservers` calls `terminate_vm` on them.
        # However, the VM (OpenStackServer) that an app server is associated with
        # *should* have ServerStatus.Terminated if the app server was old enough to be terminated.
        self._assert_status([
            (obsolete_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Terminated),
            (recent_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (newer_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
        ])

    def test_terminate_obsolete_appservers_no_active(self):
        """
        Test that `terminate_obsolete_appservers` does not terminate any app servers
        if an instance does not have an active app server.
        """
        instance = OpenEdXInstanceFactory()
        reference_date = timezone.now()

        # Create app servers
        obsolete_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=5))
        obsolete_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=5))

        recent_appserver = self._create_running_appserver(instance, reference_date - timedelta(days=1))
        recent_appserver_failed = self._create_failed_appserver(instance, reference_date - timedelta(days=1))

        appserver = self._create_running_appserver(instance, reference_date)
        appserver_failed = self._create_failed_appserver(instance, reference_date)

        newer_appserver = self._create_running_appserver(instance, reference_date + timedelta(days=3))
        newer_appserver_failed = self._create_failed_appserver(instance, reference_date + timedelta(days=3))

        # Terminate app servers
        instance.terminate_obsolete_appservers()

        # Check status of app servers (should be unchanged)
        self._assert_status([
            (obsolete_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (obsolete_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (recent_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (recent_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (appserver, AppServerStatus.Running, ServerStatus.Pending),
            (appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
            (newer_appserver, AppServerStatus.Running, ServerStatus.Pending),
            (newer_appserver_failed, AppServerStatus.ConfigurationFailed, ServerStatus.Pending),
        ])

    def test_secret_key_creation(self):
        """
        Test that we can reliably produce derived secret keys for an instance with a particular
        existing secret key.
        """
        instance = OpenEdXInstanceFactory()
        instance.secret_key_b64encoded = 'esFyh7kbvbMQiYhRx9fISJw9gkcSCStGAfOWaPu9cfc6/tMu'
        instance.save()

        self.assertEqual(
            instance.get_secret_key_for_var('THIS_IS_A_TEST'),
            '95652a974218e2efc44f99feb6f2ab89a263746688ff428ca2c898ae44111f58',
        )
        self.assertEqual(
            instance.get_secret_key_for_var('OTHER_TEST'),
            '820b455b1f0e30b75ec0514ab172c588223b010de3beacce3cd27217adc7fe60',
        )
        self.assertEqual(
            instance.get_secret_key_for_var('SUPER_SECRET'),
            '21b5271f21ee6dacfde05cd97e20739f0e73dc8a43408ef14b657bfbf718e2b4',
        )

    def test_secret_key_settings(self):
        """
        Test the YAML settings returned by SecretKeyInstanceMixin.
        """
        instance = OpenEdXInstanceFactory()
        settings = yaml.load(instance.get_secret_key_settings())

        # Test that all keys are hex-encoded strings.
        for secret_key in settings.values():
            codecs.decode(secret_key, "hex")

        # Make sure all independent secret keys are all different
        independent_secrets = set(settings[var] for var in OPENEDX_SECRET_KEYS)
        self.assertEqual(len(independent_secrets), len(OPENEDX_SECRET_KEYS))

        # Verify that API client keys are set to the matching server key.
        for to_var, from_var in OPENEDX_SHARED_KEYS.items():
            self.assertEqual(settings[to_var], settings[from_var])

    @patch_services
    def test_do_not_create_insecure_secret_keys(self, mocks):
        """
        Test that if we have a brand-new instance with no appservers, we refuse to create insecure
        keys for those appservers if we don't have a secure secret key for the instance.
        """
        instance = OpenEdXInstanceFactory()
        instance.secret_key_b64encoded = ''
        instance.save()

        expected_error_string = re.escape(
            'Attempted to create secret key for instance {}, but no master key present.'.format(instance)
        )

        # Six provides a compatibility method for assertRaisesRegex, since the method
        # is named differently between Py2k and Py3k.
        with six.assertRaisesRegex(self, ValueError, expected_error_string):
            instance.spawn_appserver()
