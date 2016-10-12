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

from unittest.mock import call, patch, Mock
from uuid import uuid4

import ddt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
import yaml

from instance.models.appserver import Status as AppServerStatus
from instance.models.instance import InstanceReference
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance, OpenEdXAppConfiguration
from instance.models.openedx_appserver import DEFAULT_EDX_PLATFORM_REPO_URL
from instance.models.server import Server
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
        self.assertEqual(instance.edx_platform_repository_url, DEFAULT_EDX_PLATFORM_REPO_URL)
        self.assertEqual(instance.edx_platform_commit, settings.DEFAULT_OPENEDX_RELEASE)
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

        mysql_user = instance.mysql_user
        mysql_pass = instance.mysql_pass
        mongo_user = instance.mongo_user
        mongo_pass = instance.mongo_pass

        instance.name = "Test Instance"
        instance.save()
        self._assert_defaults(instance, name=instance.name)

        self.assertEqual(instance.mysql_user, mysql_user)
        self.assertEqual(instance.mysql_pass, mysql_pass)
        self.assertEqual(instance.mongo_user, mongo_user)
        self.assertEqual(instance.mongo_pass, mongo_pass)

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
        # And DNS should never be changed from spawn_appserver() alone:
        self.assertEqual(mocks.mock_set_dns_record.call_count, 0)

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
        Test set_appserver_active()
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.opencraft.com',
                                          use_ephemeral_databases=True)
        appserver_id = instance.spawn_appserver()
        instance.set_appserver_active(appserver_id)
        self.assertEqual(instance.active_appserver.pk, appserver_id)
        self.assertEqual(mocks.mock_set_dns_record.mock_calls, [
            call('opencraft.com', name='test.activate', type='A', value='1.1.1.1'),
            call('opencraft.com', name='preview-test.activate', type='CNAME', value='test.activate'),
            call('opencraft.com', name='studio-test.activate', type='CNAME', value='test.activate'),
        ])

    @patch_services
    def test_set_appserver_active_external_domain(self, mocks):
        """
        Test set_appserver_active() with custom external domains.
        Ensure that the DNS records are only created for the internal domains.
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.opencraft.hosting',
                                          external_lms_domain='courses.myexternal.org',
                                          external_lms_preview_domain='preview.myexternal.org',
                                          external_studio_domain='studio.myexternal.org',
                                          use_ephemeral_databases=True)
        appserver_id = instance.spawn_appserver()
        instance.set_appserver_active(appserver_id)
        self.assertEqual(instance.active_appserver.pk, appserver_id)
        self.assertEqual(mocks.mock_set_dns_record.mock_calls, [
            call('opencraft.hosting', name='test.activate', type='A', value='1.1.1.1'),
            call('opencraft.hosting', name='preview-test.activate', type='CNAME', value='test.activate'),
            call('opencraft.hosting', name='studio-test.activate', type='CNAME', value='test.activate'),
        ])

    @patch_services
    def test_set_appserver_active_base_subdomain(self, mocks):
        """
        Test set_appserver_active() with a base domain that includes part of a
        subdomain. Ensure that the dns records include the part of the subdomain
        in the base domain of the instance.
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.stage.opencraft.hosting',
                                          use_ephemeral_databases=True)
        appserver_id = instance.spawn_appserver()
        instance.set_appserver_active(appserver_id)
        self.assertEqual(instance.active_appserver.pk, appserver_id)
        self.assertEqual(mocks.mock_set_dns_record.mock_calls, [
            call('opencraft.hosting', name='test.activate.stage', type='A', value='1.1.1.1'),
            call('opencraft.hosting', name='preview-test.activate.stage', type='CNAME', value='test.activate.stage'),
            call('opencraft.hosting', name='studio-test.activate.stage', type='CNAME', value='test.activate.stage'),
        ])

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

    @ddt.data(True, False)
    @patch_services
    @patch('instance.models.openedx_instance.OpenEdXAppServer.terminate_vm')
    @patch('instance.models.mixins.database.MySQLInstanceMixin.deprovision_mysql')
    @patch('instance.models.mixins.database.MongoDBInstanceMixin.deprovision_mongo')
    @patch('instance.models.mixins.storage.SwiftContainerInstanceMixin.deprovision_swift')
    def test_delete_instance(
            self, mocks, delete_by_ref,
            mock_deprovision_swift, mock_deprovision_mongo, mock_deprovision_mysql, mock_terminate_vm
    ):
        """
        Test that an instance can be deleted directly or by its InstanceReference,
        that the associated AppServers and VMs will be terminated,
        and that external databases and storage will be deprovisioned.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.deletion', use_ephemeral_databases=True)
        instance_ref = instance.ref
        appserver = OpenEdXAppServer.objects.get(pk=instance.spawn_appserver())

        for mocked_method in (
                mock_terminate_vm, mock_deprovision_mysql, mock_deprovision_mongo, mock_deprovision_swift
        ):
            self.assertEqual(mocked_method.call_count, 0)

        # Now delete the instance, either using InstanceReference or the OpenEdXInstance class:
        if delete_by_ref:
            instance_ref.delete()
        else:
            instance.delete()

        for mocked_method in (
                mock_terminate_vm, mock_deprovision_mysql, mock_deprovision_mongo, mock_deprovision_swift
        ):
            self.assertEqual(mocked_method.call_count, 1)

        with self.assertRaises(OpenEdXInstance.DoesNotExist):
            OpenEdXInstance.objects.get(pk=instance.pk)
        with self.assertRaises(InstanceReference.DoesNotExist):
            instance_ref.refresh_from_db()
        with self.assertRaises(OpenEdXAppServer.DoesNotExist):
            appserver.refresh_from_db()

    @staticmethod
    def _set_appserver_terminated(appserver):
        """
        Transition `appserver` to Status.Terminated.
        """
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_running()
        appserver._status_to_terminated()

    @staticmethod
    def _set_appserver_running(appserver):
        """
        Transition `appserver` to Status.Running.
        """
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_running()

    def _create_appserver(self, instance, status):
        """
        Return appserver for `instance` that has `status`.
        """
        appserver = make_test_appserver(instance)
        if status == AppServerStatus.Running:
            self._set_appserver_running(appserver)
        elif status == AppServerStatus.Terminated:
            self._set_appserver_terminated(appserver)
        return appserver

    def _create_running_appserver(self, instance):
        """
        Return running app server for `instance` that has `status` AppServerStatus.Running.
        """
        return self._create_appserver(instance, AppServerStatus.Running)

    def _create_terminated_appserver(self, instance):
        """
        Return running app server for `instance` that has `status` AppServerStatus.ConfigurationFailed.
        """
        return self._create_appserver(instance, AppServerStatus.Terminated)

    @ddt.data(
        (0, 0, False, False),  # No app servers, monitoring disabled
        (0, 0, True, False),  # No app servers, monitoring enabled
        (3, 0, False, False),  # Some running app servers, no terminated app servers, monitoring disabled
        (3, 0, True, False),  # Some running app servers, no terminated app servers, monitoring enabled
        (3, 3, False, False),  # Some running app servers, some terminated app servers, monitoring disabled
        (3, 3, True, False),  # Some running app servers, some terminated app servers, monitoring enabled
        (0, 3, False, True),  # No running app servers, some terminated app servers, monitoring disabled
        (0, 3, True, False),  # No running app servers, some terminated app servers, monitoring enabled
    )
    @ddt.unpack
    @patch('instance.models.mixins.openedx_monitoring.newrelic')
    def test_shut_down(
            self, num_running_appservers, num_terminated_appservers, monitoring_enabled, expected_result, mock_newrelic
    ):
        """
        Test that `shut_down` property correctly reports whether an instance has been shut down.

        An instance has been shut down if all of its app servers have been terminated,
        and monitoring has been turned off.
        """
        instance = OpenEdXInstanceFactory()

        for dummy in range(num_running_appservers):
            self._create_running_appserver(instance)
        for dummy in range(num_terminated_appservers):
            self._create_terminated_appserver(instance)

        if monitoring_enabled:
            monitor_id = str(uuid4())
            instance.new_relic_availability_monitors.create(pk=monitor_id)

        self.assertEqual(instance.shut_down, expected_result)
