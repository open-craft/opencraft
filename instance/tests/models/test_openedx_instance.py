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

import ddt
from django.conf import settings
from django.test import override_settings
import yaml

from instance.models.appserver import Status as AppServerStatus
from instance.models.instance import InstanceReference
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance, OpenEdXAppConfiguration
from instance.models.server import Server
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

# Factory boy doesn't properly support pylint+django
#pylint: disable=no-member

@ddt.ddt
class OpenEdXInstanceTestCase(TestCase):
    """
    Test cases for OpenEdXInstance models
    """
    @override_settings(INSTANCE_EPHEMERAL_DATABASES=True)
    def test_create_defaults(self):
        """
        Create an instance without specifying additional fields,
        leaving it up to the create method to set them
        """
        instance = OpenEdXInstance.objects.create(sub_domain='create.defaults')
        self.assertEqual(instance.name, 'Instance')
        self.assertFalse(instance.mysql_user)
        self.assertFalse(instance.mysql_pass)
        self.assertFalse(instance.mongo_user)
        self.assertFalse(instance.mongo_pass)
        self.assertFalse(instance.swift_openstack_user)
        self.assertFalse(instance.swift_openstack_password)
        self.assertFalse(instance.swift_openstack_tenant)
        self.assertFalse(instance.swift_openstack_auth_url)
        self.assertFalse(instance.swift_openstack_region)
        self.assertEqual(instance.github_admin_organization_name, '')

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=False)
    def test_create_defaults_persistent_databases(self):
        """
        Create an instance without specifying additional fields,
        leaving it up to the create method to set them
        """
        instance = OpenEdXInstance.objects.create(sub_domain='create.defaults')
        self.assertEqual(instance.name, 'Instance')
        self.assertTrue(instance.mysql_user)
        self.assertTrue(instance.mysql_pass)
        self.assertTrue(instance.mongo_user)
        self.assertTrue(instance.mongo_pass)
        self.assertEqual(instance.swift_openstack_user, settings.SWIFT_OPENSTACK_USER)
        self.assertEqual(instance.swift_openstack_password, settings.SWIFT_OPENSTACK_PASSWORD)
        self.assertEqual(instance.swift_openstack_tenant, settings.SWIFT_OPENSTACK_TENANT)
        self.assertEqual(instance.swift_openstack_auth_url, settings.SWIFT_OPENSTACK_AUTH_URL)
        self.assertEqual(instance.swift_openstack_region, settings.SWIFT_OPENSTACK_REGION)
        self.assertEqual(instance.github_admin_organization_name, '')

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
            base_domain='example.org', sub_domain='sample', name='Sample Instance'
        )
        self.assertEqual(instance.domain, 'sample.example.org')
        self.assertEqual(instance.url, 'http://sample.example.org/')
        self.assertEqual(instance.lms_preview_domain, 'preview-sample.example.org')
        self.assertEqual(instance.lms_preview_url, 'http://preview-sample.example.org/')
        self.assertEqual(instance.studio_domain, 'studio-sample.example.org')
        self.assertEqual(instance.studio_url, 'http://studio-sample.example.org/')
        self.assertEqual(str(instance), 'Sample Instance (sample.example.org)')

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

    @patch_services
    def test_set_appserver_active(self, mocks):
        """
        Test set_appserver_active()
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.activate', use_ephemeral_databases=True)
        appserver_id = instance.spawn_appserver()
        instance.set_appserver_active(appserver_id)
        self.assertEqual(instance.active_appserver.pk, appserver_id)
        self.assertEqual(mocks.mock_set_dns_record.mock_calls, [
            call(name='test.activate', type='A', value='1.1.1.1'),
            call(name='preview-test.activate', type='CNAME', value='test.activate'),
            call(name='studio-test.activate', type='CNAME', value='test.activate'),
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
    def test_delete_instance(self, mocks, delete_by_ref, mock_terminate_vm):
        """
        Test that an instance can be deleted directly or by its InstanceReference, and that the
        associated AppServers and VMs will be terminated.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.deletion', use_ephemeral_databases=False)
        instance_ref = instance.ref
        appserver = OpenEdXAppServer.objects.get(pk=instance.spawn_appserver())

        self.assertEqual(mock_terminate_vm.call_count, 0)

        # Now delete the instance, either using InstanceReference or the OpenEdXInstance class:
        if delete_by_ref:
            instance_ref.delete()
        else:
            instance.delete()

        self.assertEqual(mock_terminate_vm.call_count, 1)
        with self.assertRaises(OpenEdXInstance.DoesNotExist):
            OpenEdXInstance.objects.get(pk=instance.pk)
        with self.assertRaises(InstanceReference.DoesNotExist):
            instance_ref.refresh_from_db()
        with self.assertRaises(OpenEdXAppServer.DoesNotExist):
            appserver.refresh_from_db()
