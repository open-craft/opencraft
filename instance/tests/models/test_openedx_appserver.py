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
OpenEdXAppServer model - Tests
"""

# Imports #####################################################################

import os
from unittest.mock import patch, Mock, PropertyMock

import novaclient
import requests
import responses
import yaml
from ddt import ddt, data
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail as django_mail
from django.test import override_settings
from freezegun import freeze_time
from pytz import utc

from instance.models.appserver import Status as AppServerStatus, AppServer
from instance.models.mixins.ansible import Playbook
from instance.models.openedx_appserver import OpenEdXAppServer, OPENEDX_APPSERVER_SECURITY_GROUP_RULES
from instance.models.server import Server
from instance.models.utils import WrongStateException
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services
from userprofile.factories import make_user_and_organization, OrganizationFactory
from userprofile.models import Organization


# Tests #######################################################################

@ddt
@patch(
    'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class OpenEdXAppServerTestCase(TestCase):
    """
    Test cases for OpenEdXAppServer objects
    """

    def test_immutable_fields(self, mock_consul):
        """
        Test that some appserver fields are immutable.
        """
        appserver = make_test_appserver()
        appserver.openedx_release = "open-release/zelkova"
        with self.assertRaises(RuntimeError):
            appserver.save(update_fields=["openedx_release"])

    def test_get_playbooks(self, mock_consul):
        """
        Verify correct list of playbooks is provided for spawning an appserver.
        """
        instance = OpenEdXInstanceFactory()
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        instance.lms_users.add(user)
        appserver = make_test_appserver(instance)
        # By default there should be four playbooks:
        # - OpenEdX provisioning playbook,
        # - LMS users playbook,
        # - enable bulk emails playbook,
        # - and the OCIM service ansible playbook.
        playbooks = appserver.get_playbooks()
        self.assertEqual(len(playbooks), 4)
        self.assertEqual(playbooks[0], appserver.default_playbook())
        self.assertEqual(playbooks[1], appserver.lms_user_creation_playbook())
        self.assertEqual(playbooks[2], appserver.enable_bulk_emails_playbook())
        self.assertEqual(playbooks[3].source_repo, settings.ANSIBLE_APPSERVER_REPO)
        self.assertEqual(playbooks[3].playbook_path, settings.ANSIBLE_APPSERVER_PLAYBOOK)
        # Once the instance has been successfully provisioned, the "enable bulk emails" playbooks is no longer run.
        instance.successfully_provisioned = True
        instance.save()
        playbooks = appserver.get_playbooks()
        self.assertEqual(len(playbooks), 3)
        self.assertTrue(appserver.enable_bulk_emails_playbook() not in playbooks)

    @patch_services
    def test_provision(self, mocks, mock_consul):
        """
        Run provisioning sequence
        """
        mocks.mock_run_ansible_playbooks.return_value = (['log'], 0)
        mocks.mock_create_server.side_effect = [Mock(id='test-run-provisioning-server'), None]
        mocks.os_server_manager.add_fixture('test-run-provisioning-server', 'openstack/api_server_2_active.json')
        mock_reboot = mocks.os_server_manager.get_os_server('test-run-provisioning-server').reboot

        appserver = make_test_appserver()
        self.assertEqual(appserver.status, AppServerStatus.New)
        self.assertEqual(appserver.server.status, Server.Status.Pending)
        result = appserver.provision()
        self.assertTrue(result)
        self.assertEqual(appserver.status, AppServerStatus.Running)
        self.assertEqual(appserver.server.status, Server.Status.Ready)
        self.assertEqual(mocks.mock_run_ansible_playbooks.call_count, 1)
        self.assertEqual(mock_reboot.call_count, 1)

    @patch_services
    def test_provision_build_failed(self, mocks, mock_consul):
        """
        Run provisioning sequence failing server creation on purpose to make sure
        server and instance statuses will be set accordingly.
        """
        appserver = make_test_appserver()
        self.assertEqual(appserver.status, AppServerStatus.New)
        self.assertEqual(appserver.server.status, Server.Status.Pending)

        mocks.mock_create_server.side_effect = novaclient.exceptions.ClientException(400)
        result = appserver.provision()
        self.assertFalse(result)

        self.assertEqual(appserver.status, AppServerStatus.Error)
        self.assertEqual(appserver.server.status, Server.Status.BuildFailed)
        mocks.mock_provision_failed_email.assert_called_once_with('Unable to start an OpenStack server')

    @patch_services
    def test_provision_failed(self, mocks, mock_consul):
        """
        Run provisioning sequence failing the deployment on purpose to make sure
        server and instance statuses will be set accordingly.
        """
        log_lines = ['log']
        mocks.mock_run_ansible_playbooks.return_value = (log_lines, 1)
        appserver = make_test_appserver()
        self.assertEqual(appserver.status, AppServerStatus.New)
        self.assertEqual(appserver.server.status, Server.Status.Pending)
        result = appserver.provision()
        self.assertFalse(result)
        self.assertEqual(appserver.status, AppServerStatus.ConfigurationFailed)
        self.assertEqual(appserver.server.status, Server.Status.Ready)
        mocks.mock_provision_failed_email.assert_called_once_with(
            "AppServer deploy failed: Ansible play exited with non-zero exit code", log_lines
        )

    @patch_services
    def test_provision_unhandled_exception(self, mocks, mock_consul):
        """
        Make sure that if there is an unhandled exception during provisioning, the provision()
        method should return False and send an email.
        """
        mocks.mock_run_ansible_playbooks.side_effect = Exception('Something went catastrophically wrong')
        appserver = make_test_appserver()
        result = appserver.provision()
        self.assertFalse(result)
        mocks.mock_provision_failed_email.assert_called_once_with("AppServer deploy failed: unhandled exception")

    def test_admin_users(self, mock_consul):
        """
        By default, all users that belong to an organization that owns the
        server and OCIM admins have access to the sandbox.
        """
        admin_org_handle = 'admin-org'
        OrganizationFactory(name=admin_org_handle, github_handle=admin_org_handle)

        users = [
            ('user', 'user', admin_org_handle),
            ('admin2', 'admin2', admin_org_handle),
            ('no_github_handle', '', admin_org_handle),
            ('inactive_user', 'inactive_user', admin_org_handle),
            ('another_org', 'another_org', 'another_org'),
            ('no_org_1', 'no_org_1', ''),
            ('no_org_2', 'no_org_2', None),
        ]
        admin_users = [
            ('admin1', 'admin1', admin_org_handle),
            ('admin3', 'admin3', 'another_org'),
            ('admin4', 'admin4', ''),
            ('admin5', 'admin5', None),
            ('admin_no_org', '', admin_org_handle),
            ('admin_no_github', 'invalid_github_user', admin_org_handle),
            ('inactive_admin', 'inactive_admin', admin_org_handle),
        ]

        expected_admin_users = ['user', 'admin1', 'admin2', 'admin3', 'admin4', 'admin5']

        for username, github_handle, org_handle in users:
            make_user_and_organization(username, github_username=github_handle, org_handle=org_handle)

        for username, github_handle, org_handle in admin_users:
            profile, _ = make_user_and_organization(username, github_username=github_handle, org_handle=org_handle)
            profile.user.is_superuser = True
            profile.user.save()

        # Mark the inactive user and admin as inactive; they should not be added to the resulting list
        get_user_model().objects.filter(username__in=('inactive_user', 'inactive_admin')).update(is_active=False)

        def check(_users):
            return [_user for _user in _users if _user != 'invalid_github_user']

        with patch('instance.models.mixins.openedx_config.check_github_users', check):
            appserver = make_test_appserver(
                OpenEdXInstanceFactory(),
                organization=Organization.objects.get(github_handle=admin_org_handle),
            )

            # Check user with non existant Github hande is removed
            self.assertEqual(len(appserver.admin_users) - 1, len(expected_admin_users))

            ansible_settings = yaml.load(appserver.configuration_settings, Loader=yaml.SafeLoader)
            self.assertCountEqual(ansible_settings['COMMON_USER_INFO'], [
                {'name': name, 'github': True, 'type': 'admin'} for name in expected_admin_users
            ])

    @patch_services
    def test_cannot_reprovision(self, mocks, mock_consul):
        """
        Once an AppServer's provision() method has been called once, it cannot be called ever
        again. Instead, a new AppServer must be created.
        """
        app_server = make_test_appserver()
        self.assertEqual(app_server.status, AppServerStatus.New)

        app_server.provision()
        self.assertEqual(app_server.status, AppServerStatus.Running)

        with self.assertRaises(WrongStateException):
            app_server.provision()

        # Double-check for various states other than New:
        invalid_from_states = (
            AppServerStatus.WaitingForServer,
            AppServerStatus.ConfiguringServer,
            AppServerStatus.Error,
            AppServerStatus.ConfigurationFailed,
            AppServerStatus.Running,
            AppServerStatus.Terminated
        )
        for invalid_from_state in invalid_from_states:
            # Hack to force the app server into a specific state:
            OpenEdXAppServer.objects.filter(pk=app_server.pk).update(_status=invalid_from_state.state_id)
            app_server = OpenEdXAppServer.objects.get(pk=app_server.pk)
            with self.assertRaises(WrongStateException):
                app_server.provision()

    @patch('instance.openstack_utils.get_nova_client')
    def test_launch_in_other_region(self, mock_get_nova_client, mock_consul):
        """
        Test launching an appserver in a non-default region.
        """
        instance = OpenEdXInstanceFactory(openstack_region="elsewhere")
        make_test_appserver(instance)
        mock_get_nova_client.assert_called_once_with("elsewhere")

    @data(
        'ANALYTICS_API_VERSION',
        'DISCOVERY_VERSION',
        'ECOMMERCE_VERSION',
        'INSIGHTS_VERSION',
        'NOTIFIER_VERSION',
    )
    def test_default_component_versions(self, component_version, mock_consul):
        """
        Test the default value of components' version
        """
        instance = OpenEdXInstanceFactory(
            name='Vars Instance',
            email='vars@example.com',
            openedx_release='dummy-release'
        )
        appserver = make_test_appserver(instance)
        self.assertIn(
            '{}: dummy-release'.format(component_version), appserver.configuration_settings
        )

    @data(
        'ANALYTICS_API_VERSION',
        'DISCOVERY_VERSION',
        'ECOMMERCE_VERSION',
        'INSIGHTS_VERSION',
        'NOTIFIER_VERSION',
    )
    def test_component_versions_on_override(self, component_version, mock_consul):
        """
        Test the components' version values on override
        """
        extra_configuration = """
        {}: dummy-release
        """.format(component_version)
        instance = OpenEdXInstanceFactory(
            name='Vars Instance',
            email='vars@example.com',
            openedx_release='open-release/ginkgo.2',
            configuration_extra_settings=extra_configuration,
        )
        appserver = make_test_appserver(instance)
        self.assertIn(
            '{}: dummy-release'.format(component_version), appserver.configuration_settings
        )

    def test_configuration_extra_settings(self, mock_consul):
        """
        Add extra settings in ansible vars, which can override existing settings
        """
        instance = OpenEdXInstanceFactory(
            name='Vars Instance',
            email='vars@example.com',
            configuration_extra_settings='EDXAPP_PLATFORM_NAME: "Overridden!"',
        )
        appserver = make_test_appserver(instance)
        self.assertIn('EDXAPP_PLATFORM_NAME: Overridden!', appserver.configuration_settings)
        self.assertNotIn('Vars Instance', appserver.configuration_settings)
        self.assertIn("EDXAPP_CONTACT_EMAIL: vars@example.com", appserver.configuration_settings)

    def test_lms_user_settings(self, mock_consul):
        """
        Test that lms_user_settings are initialised correctly for new AppServers.
        """
        instance = OpenEdXInstanceFactory()
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        instance.lms_users.add(user)
        appserver = make_test_appserver(instance)
        ansible_settings = yaml.load(appserver.lms_user_settings, Loader=yaml.SafeLoader)
        self.assertEqual(len(ansible_settings['django_users']), 1)
        self.assertEqual(ansible_settings['django_users'][0]['username'], user.username)
        self.assertEqual(ansible_settings['django_groups'], [])

    @override_settings(
        INSTANCE_SMTP_RELAY_HOST='smtp.myhost.com',
        INSTANCE_SMTP_RELAY_PORT=2525,
        INSTANCE_SMTP_RELAY_USERNAME='smtpuser',
        INSTANCE_SMTP_RELAY_PASSWORD='smtppass',
        INSTANCE_SMTP_RELAY_SENDER_DOMAIN='opencraft.hosting'
    )
    def test_postfix_queue_settings_present(self, mock_consul):
        """
        Check that ansible vars for postfix_queue role are set correctly.
        """
        instance = OpenEdXInstanceFactory(
            sub_domain='test.postfix.queue',
            email='test.postfix@myinstance.org',
            external_lms_domain='lms.myinstance.org'
        )
        appserver = make_test_appserver(instance)
        configuration_vars = yaml.load(appserver.configuration_settings, Loader=yaml.SafeLoader)
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_EXTERNAL_SMTP_HOST'], 'smtp.myhost.com')
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_EXTERNAL_SMTP_PORT'], '2525')
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_EXTERNAL_SMTP_USER'], 'smtpuser')
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_EXTERNAL_SMTP_PASSWORD'], 'smtppass')
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_HEADER_CHECKS'], '/^From:(.*)$/   PREPEND Reply-To:$1')
        self.assertEqual(
            configuration_vars['POSTFIX_QUEUE_SENDER_CANONICAL_MAPS'],
            '@myinstance.org  lms.myinstance.org@opencraft.hosting'
        )

    @override_settings(INSTANCE_SMTP_RELAY_HOST=None)
    def test_postfix_queue_settings_absent(self, mock_consul):
        """
        Check that ansible vars for postfix_queue role are not present when SMTP relay host is not configured.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.no.postfix.queue')
        appserver = make_test_appserver(instance)
        configuration_vars = yaml.load(appserver.configuration_settings, Loader=yaml.SafeLoader)
        self.assertNotIn('POSTFIX_QUEUE_EXTERNAL_SMTP_HOST', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_EXTERNAL_SMTP_PORT', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_EXTERNAL_SMTP_USER', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_EXTERNAL_SMTP_PASSWORD', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_HEADER_CHECKS', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_SENDER_CANONICAL_MAPS', configuration_vars)

    def test_youtube_api_key_unset(self, mock_consul):
        """
        Check that EDXAPP_YOUTUBE_API_KEY is set to None by default.
        """
        instance = OpenEdXInstanceFactory(sub_domain='youtube.apikey')
        appserver = make_test_appserver(instance)
        configuration_vars = yaml.load(appserver.configuration_settings, Loader=yaml.SafeLoader)
        self.assertIsNone(configuration_vars['EDXAPP_YOUTUBE_API_KEY'])

    @patch_services
    def test_default_security_groups(self, mocks, mock_consul):
        """
        Test that security groups are set when provisioning an AppServer
        """
        result = make_test_appserver().provision()
        self.assertTrue(result)
        create_server_kwargs = mocks.mock_create_server.call_args[1]
        self.assertEqual(create_server_kwargs["security_groups"], [settings.OPENEDX_APPSERVER_SECURITY_GROUP_NAME])

    @override_settings(OPENEDX_APPSERVER_SECURITY_GROUP_NAME="default-group")
    @patch_services
    def test_additional_security_groups(self, mocks, mock_consul):
        """
        Test a differently-named default security group, as well as the ability
        for an Instance to specify additional security groups.
        """
        instance = OpenEdXInstanceFactory(additional_security_groups=["group_a", "group_b"])
        app_server = make_test_appserver(instance)
        result = app_server.provision()
        self.assertTrue(result)
        create_server_kwargs = mocks.mock_create_server.call_args[1]
        self.assertEqual(create_server_kwargs["security_groups"], ["default-group", "group_a", "group_b"])

    @patch_services
    def test_provision_invalid_security_groups(self, mocks, mock_consul):
        """
        Test what happens when security groups cannot be created/synced/verified.
        The server VM should not be created, and the provisioning should fail.
        """
        mocks.mock_check_security_groups.side_effect = Exception("Testing security group update failure")
        app_server = make_test_appserver()
        result = app_server.provision()
        self.assertFalse(result)
        mocks.mock_create_server.assert_not_called()
        mocks.mock_provision_failed_email.assert_called_once_with(
            "Unable to check/update the network security groups for the new VM"
        )

    @patch("instance.models.openedx_appserver.get_openstack_connection")
    @patch("instance.models.openedx_appserver.sync_security_group_rules")
    def test_check_security_groups(self, mock_sync_security_group_rules, mock_get_openstack_connection, mock_consul):
        """
        Test that check_security_groups() can create and synchronize security groups
        """
        # We simulate the existence of these network security groups on the OpenStack cloud:
        existing_groups = ["group_a", "group_b"]
        new_security_group = Mock()

        def mocked_find_security_group(name_or_id):
            """ Mock openstack network.find_security_group """
            if name_or_id in existing_groups:
                result = Mock()
                result.name = name_or_id
                return result
            else:
                return None

        def mocked_create_security_group(**args):
            """ Mock openstack network.create_security_group """
            new_security_group.__dict__.update(**args)
            return new_security_group

        network = mock_get_openstack_connection().network
        network.find_security_group.side_effect = mocked_find_security_group
        network.create_security_group.side_effect = mocked_create_security_group

        instance = OpenEdXInstanceFactory(additional_security_groups=["group_a", "group_b"])
        app_server = make_test_appserver(instance)

        # Call check_security_groups():
        app_server.check_security_groups()
        # the default group doesn't exist, so we expect it was created:
        network.create_security_group.assert_called_once_with(name=settings.OPENEDX_APPSERVER_SECURITY_GROUP_NAME)
        # we also expect that its description was set:
        expected_description = "Security group for Open EdX AppServers. Managed automatically by OpenCraft IM."
        network.update_security_group.assert_called_once_with(new_security_group, description=expected_description)
        # We expect that the group was synced with the configured rules:
        mock_sync_security_group_rules.assert_called_once_with(
            new_security_group, OPENEDX_APPSERVER_SECURITY_GROUP_RULES, network=network
        )

        # Now, if we change the additional groups, we expect to get an exception:
        instance.additional_security_groups = ["invalid"]
        instance.save()
        app_server = make_test_appserver(instance)
        with self.assertRaisesRegex(Exception, "Unable to find the OpenStack network security group called 'invalid'."):
            app_server.check_security_groups()

    @patch_services
    def test_default_openstack_settings(self, mocks, mock_consul):
        """
        Test that the default openstack settings are used when starting an appserver
        """
        result = make_test_appserver().provision()
        self.assertTrue(result)
        create_server_kwargs = mocks.mock_create_server.call_args[1]
        self.assertEqual(create_server_kwargs["flavor_selector"], settings.OPENSTACK_SANDBOX_FLAVOR)
        self.assertEqual(create_server_kwargs["image_selector"], settings.OPENSTACK_SANDBOX_BASE_IMAGE)
        self.assertEqual(create_server_kwargs["key_name"], settings.OPENSTACK_SANDBOX_SSH_KEYNAME)

    @patch_services
    def test_custom_openstack_settings(self, mocks, mock_consul):
        """
        Test that the instance's custom openstack settings are used when starting an appserver.
        """
        flavor_selector = {'name': 'another-flavor'}
        image_selector = {'name': 'another-image'}
        key_name = 'another-key'
        instance = OpenEdXInstanceFactory(
            openstack_server_flavor=flavor_selector,
            openstack_server_base_image=image_selector,
            openstack_server_ssh_keyname=key_name,
        )
        app_server = make_test_appserver(instance)
        result = app_server.provision()
        self.assertTrue(result)
        create_server_kwargs = mocks.mock_create_server.call_args[1]
        self.assertEqual(create_server_kwargs["flavor_selector"], flavor_selector)
        self.assertEqual(create_server_kwargs["image_selector"], image_selector)
        self.assertEqual(create_server_kwargs["key_name"], key_name)

    @patch_services
    def test_is_active(self, *mocks):
        """
        Test is_active property and setter
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.opencraft.co.uk')
        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)

        self.assertEqual(instance.appserver_set.get().last_activated, None)

        with freeze_time('2017-01-17 11:25:00') as freezed_time:
            appserver.is_active = True
        activation_time = utc.localize(freezed_time())
        self.assertTrue(appserver.is_active)

        # Re-activating doesn't change the date, since no change was made.
        appserver.is_active = True
        self.assertTrue(appserver.is_active)
        self.assertEqual(appserver.last_activated, activation_time)

        self.assertEqual(appserver.last_activated, activation_time)

        # Deactivating does not change last_activated time
        appserver.is_active = False
        self.assertFalse(appserver.is_active)
        self.assertEqual(appserver.last_activated, activation_time)

        # Re-deactivating is ok too
        appserver.is_active = False
        self.assertFalse(appserver.is_active)
        self.assertEqual(appserver.last_activated, activation_time)

    @override_settings(DISABLE_LOAD_BALANCER_CONFIGURATION=False)
    @patch_services
    def test_make_active(self, mocks, mock_consul):
        """
        Test make_active() and make_active(active=False)
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.opencraft.co.uk')
        appserver_id = instance.spawn_appserver()
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 1)
        appserver = instance.appserver_set.get(pk=appserver_id)

        self.assertEqual(instance.appserver_set.get().last_activated, None)

        with freeze_time('2017-01-17 11:25:00') as freezed_time:
            appserver.make_active()
        activation_time = utc.localize(freezed_time())

        instance.refresh_from_db()
        appserver.refresh_from_db()
        self.assertTrue(appserver.is_active)
        self.assertEqual(appserver.last_activated, activation_time)
        self.assertEqual(instance.appserver_set.get().last_activated, activation_time)
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 2)
        self.assertEqual(mocks.mock_enable_monitoring.call_count, 1)
        self.assertEqual(mocks.mock_run_appserver_playbooks.call_count, 1)

        # Test deactivate
        appserver.make_active(active=False)
        instance.refresh_from_db()
        appserver.refresh_from_db()
        self.assertFalse(appserver.is_active)
        self.assertEqual(appserver.last_activated, activation_time)
        self.assertFalse(instance.get_active_appservers().exists())
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 3)
        self.assertEqual(mocks.mock_disable_monitoring.call_count, 0)
        self.assertEqual(mocks.mock_run_appserver_playbooks.call_count, 2)

    @patch_services
    @override_settings(DISABLE_LOAD_BALANCER_CONFIGURATION=False)
    def test_make_active_fails_to_start_services(self, mocks, mock_consul):
        """
        Test make_active() and check if it's behaving correctly when the
        playbooks to start services fail
        """
        mocks.mock_run_appserver_playbooks.return_value = ('', 2)
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.opencraft.co.uk')
        appserver_id = instance.spawn_appserver()
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 1)
        appserver = instance.appserver_set.get(pk=appserver_id)

        self.assertEqual(instance.appserver_set.get().last_activated, None)

        appserver.make_active()

        instance.refresh_from_db()
        appserver.refresh_from_db()
        self.assertEqual(mocks.mock_run_appserver_playbooks.call_count, 1)
        self.assertFalse(appserver.is_active)
        self.assertEqual(appserver.last_activated, None)
        self.assertEqual(instance.appserver_set.get().last_activated, None)
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 1)
        self.assertEqual(mocks.mock_enable_monitoring.call_count, 0)

    @patch_services
    @override_settings(DISABLE_LOAD_BALANCER_CONFIGURATION=True)
    def test_make_active_no_load_balancer_reconfiguration(self, mocks, mock_consul):
        """
        Test make_active() and make_active(active=False) when the load balancer
        reconfiguration is disabled
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.opencraft.co.uk')
        appserver_id = instance.spawn_appserver()
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 0)
        appserver = instance.appserver_set.get(pk=appserver_id)

        self.assertEqual(instance.appserver_set.get().last_activated, None)

        with freeze_time('2017-01-17 11:25:00') as freezed_time:
            appserver.make_active()
        activation_time = utc.localize(freezed_time())

        instance.refresh_from_db()
        appserver.refresh_from_db()
        self.assertTrue(appserver.is_active)
        self.assertEqual(appserver.last_activated, activation_time)
        self.assertEqual(instance.appserver_set.get().last_activated, activation_time)
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 0)
        self.assertEqual(mocks.mock_enable_monitoring.call_count, 1)

        # Test deactivate
        appserver.make_active(active=False)
        instance.refresh_from_db()
        appserver.refresh_from_db()
        self.assertFalse(appserver.is_active)
        self.assertEqual(appserver.last_activated, activation_time)
        self.assertFalse(instance.get_active_appservers().exists())
        self.assertEqual(mocks.mock_load_balancer_run_playbook.call_count, 0)
        self.assertEqual(mocks.mock_disable_monitoring.call_count, 0)

    @override_settings(SITE_ROOT="/root/dir/")
    @patch_services
    def test_manage_instance_services(self, mocks, mock_consul):
        """
        Test if manage instance services is correctly running the playbook
        """
        instance = OpenEdXInstanceFactory(internal_lms_domain='test.activate.opencraft.co.uk')
        appserver_id = instance.spawn_appserver()
        appserver = instance.appserver_set.get(pk=appserver_id)
        expected_playbook = Playbook(
            version=None,
            source_repo=os.path.join(settings.SITE_ROOT, 'playbooks/manage_services'),
            playbook_path='manage_services.yml',
            requirements_path='requirements.txt',
            variables='services: all\nsupervisord_action: start\n'
        )

        appserver.manage_instance_services(active=True)

        self.assertEqual(mocks.mock_run_appserver_playbooks.call_count, 1)
        mocks.mock_run_appserver_playbooks.assert_called_once_with(
            playbook=expected_playbook,
            working_dir=expected_playbook.source_repo,
        )

    @patch_services
    def test_terminate_vm(self, mocks, mock_consul):
        """
        Test AppServer termination
        """
        # Test New AppServer termination
        appserver = make_test_appserver()
        appserver.terminate_vm()
        self.assertIsNone(appserver.terminated)

        # Test Waiting for server AppServer termination
        appserver = make_test_appserver()
        appserver._status_to_waiting_for_server()
        appserver.terminate_vm()
        self.assertIsNone(appserver.terminated)

        # Test Configuring server AppServer termination
        appserver = make_test_appserver()
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver.terminate_vm()
        self.assertIsNone(appserver.terminated)

        # Test Error server AppServer termination
        appserver = make_test_appserver()
        appserver._status_to_waiting_for_server()
        appserver._status_to_error()
        appserver.terminate_vm()
        self.assertIsNone(appserver.terminated)

        # Test Failed configuring server AppServer termination
        appserver = make_test_appserver()
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_configuration_failed()
        appserver.terminate_vm()
        self.assertIsNone(appserver.terminated)

        # Test Configuring server AppServer termination
        appserver = make_test_appserver()
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_running()

        with freeze_time('2017-01-17 11:25:00') as freezed_time:
            appserver.terminate_vm()
        termination_time = utc.localize(freezed_time())

        self.assertEqual(appserver.terminated, termination_time)

        # Test terminated server AppServer termination
        appserver = make_test_appserver()
        appserver._status_to_waiting_for_server()
        appserver._status_to_configuring_server()
        appserver._status_to_running()

        with freeze_time('2017-01-18 11:25:00') as freezed_time:
            appserver.terminate_vm()
        first_termination_time = utc.localize(freezed_time())

        self.assertEqual(appserver.status, AppServer.Status.Terminated)
        appserver.terminate_vm()
        self.assertEqual(appserver.terminated, first_termination_time)


@ddt
@patch(
    'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class OpenEdXAppServerStatusTestCase(TestCase):
    """
    Test cases for status switching in OpenEdXAppServer objects
    """

    def _assert_status_conditions(self, app_server, is_steady_state=True, is_healthy_state=True):
        """
        Assert that status conditions for app_server hold as specified
        """
        self.assertEqual(app_server.status.is_steady_state, is_steady_state)
        self.assertEqual(app_server.status.is_healthy_state, is_healthy_state)

    def test_status_transitions(self, mock_consul):
        """
        Test that status transitions work as expected for different app server workflows
        """
        # Normal workflow
        app_server = make_test_appserver()
        self.assertEqual(app_server.status, AppServerStatus.New)
        self._assert_status_conditions(app_server)

        app_server._status_to_waiting_for_server()
        self.assertEqual(app_server.status, AppServerStatus.WaitingForServer)
        self._assert_status_conditions(app_server, is_steady_state=False)

        app_server._status_to_configuring_server()
        self.assertEqual(app_server.status, AppServerStatus.ConfiguringServer)
        self._assert_status_conditions(app_server, is_steady_state=False)

        app_server._status_to_running()
        self.assertEqual(app_server.status, AppServerStatus.Running)
        self._assert_status_conditions(app_server)

        app_server._status_to_terminated()
        self.assertEqual(app_server.status, AppServerStatus.Terminated)
        self._assert_status_conditions(app_server)

        # Server creation fails
        app_server_bad_server = make_test_appserver()
        app_server_bad_server._status_to_waiting_for_server()
        app_server_bad_server._status_to_error()
        self.assertEqual(app_server_bad_server.status, AppServerStatus.Error)
        self._assert_status_conditions(app_server_bad_server, is_healthy_state=False)

        # Provisioning fails
        app_server_provisioning_failed = make_test_appserver()
        app_server_provisioning_failed._status_to_waiting_for_server()
        app_server_provisioning_failed._status_to_configuring_server()
        app_server_provisioning_failed._status_to_configuration_failed()
        self.assertEqual(app_server_provisioning_failed.status, AppServerStatus.ConfigurationFailed)
        self._assert_status_conditions(app_server_provisioning_failed, is_healthy_state=False)

    @data(
        {
            'name': '_status_to_waiting_for_server',
            'from_states': [
                AppServerStatus.New,
                AppServerStatus.Error,
                AppServerStatus.ConfigurationFailed,
                AppServerStatus.Running,
                AppServerStatus.Terminated,
            ],
        },
        {
            'name': '_status_to_error',
            'from_states': [AppServerStatus.WaitingForServer],
        },
        {
            'name': '_status_to_configuring_server',
            'from_states': [AppServerStatus.WaitingForServer],
        },
        {
            'name': '_status_to_configuration_failed',
            'from_states': [AppServerStatus.ConfiguringServer],
        },
        {
            'name': '_status_to_running',
            'from_states': [AppServerStatus.ConfiguringServer],
        },
        {
            'name': '_status_to_terminated',
            'from_states': [AppServerStatus.Running],
        },
    )
    def test_invalid_status_transitions(self, transition, mock_consul):
        """
        Test that invalid status transitions raise exception
        """
        # pylint incorrectly concludes states is not iterable
        invalid_from_states = (state for state in AppServerStatus.states  # pylint: disable=not-an-iterable
                               if state not in transition['from_states'])
        for invalid_from_state in invalid_from_states:
            appserver = make_test_appserver()
            # Hack to force the status:
            OpenEdXAppServer.objects.filter(pk=appserver.pk).update(_status=invalid_from_state.state_id)
            appserver = OpenEdXAppServer.objects.get(pk=appserver.pk)
            self.assertEqual(appserver.status, invalid_from_state)
            with self.assertRaises(WrongStateException):
                getattr(appserver, transition['name'])()


@patch(
    'instance.models.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
    return_value=(1, True)
)
class EmailMixinInstanceTestCase(TestCase):
    """
    Test cases for EmailMixin
    """

    def _assert_called(self, mock, call_count=1):
        """
        Helper method - asserts that mock was called `call_count` times
        """
        self.assertTrue(mock.called)
        self.assertEqual(len(mock.call_args_list), call_count)

    def _get_call_arguments(self, mock, call_index=0):
        """
        Helper method - returns args and kwargs for `call_number`-th call
        """
        self.assertGreaterEqual(len(mock.call_args_list), call_index + 1)
        args, unused_kwargs = mock.call_args_list[call_index]
        return args

    def _check_email_attachment(self, args, name, content_parts, mimetype=None):
        """
        Checks that `email.attach` arguments are as expected
        """
        attachment_name, attachment_content, attachment_mime = args

        self.assertEqual(attachment_name, name)
        for part in content_parts:
            self.assertIn(part, attachment_content)

        if mimetype:
            self.assertEqual(attachment_mime, mimetype)

    @override_settings(ADMINS=(("admin1", "admin1@localhost"),))
    def test_provision_failed_email(self, mock_consul):
        """
        Tests that provision_failed sends email when called from normal program flow
        """
        additional_monitoring_emails = ['additionalmonitoring@localhost']
        failure_emails = ['provisionfailed@localhost']

        appserver = make_test_appserver()
        appserver.instance.additional_monitoring_emails = additional_monitoring_emails
        appserver.instance.provisioning_failure_notification_emails = failure_emails
        reason = "something went wrong"
        log_lines = ["log line1", "log_line2"]

        appserver.provision_failed_email(reason, log_lines)

        expected_subject = OpenEdXAppServer.EmailSubject.PROVISION_FAILED.format(
            name=appserver.name, instance_name=appserver.instance.name,
        )
        # failure_emails isn't included here because they get a different type of email (an urgent one)
        expected_recipients = [admin_tuple[1] for admin_tuple in settings.ADMINS]

        self.assertEqual(len(django_mail.outbox), 1)
        mail = django_mail.outbox[0]

        self.assertIn(expected_subject, mail.subject)
        self.assertIn(appserver.name, mail.body)
        self.assertIn(appserver.instance.name, mail.body)
        self.assertIn(reason, mail.body)
        self.assertEqual(mail.from_email, settings.SERVER_EMAIL)
        self.assertEqual(mail.to, expected_recipients)

        self.assertEqual(len(mail.attachments), 1)
        self.assertEqual(mail.attachments[0], ("provision.log", "\n".join(log_lines), "text/plain"))

    @override_settings(ADMINS=(
        ("admin1", "admin1@localhost"),
        ("admin2", "admin2@localhost"),
    ))
    def test_provision_failed_exception_email(self, mock_consul):
        """
        Tests that provision_failed sends email when called from exception handler
        """
        appserver = make_test_appserver()
        reason = "something went wrong"
        log_lines = ["log line1", "log_line2"]

        exception_message = "Something Bad happened Unexpectedly"
        exception = Exception(exception_message)
        try:
            raise exception
        except Exception:  # pylint: disable=broad-except
            appserver.provision_failed_email(reason, log_lines)

        expected_subject = OpenEdXAppServer.EmailSubject.PROVISION_FAILED.format(
            name=appserver.name, instance_name=appserver.instance.name,
        )
        expected_recipients = [admin_tuple[1] for admin_tuple in settings.ADMINS]

        self.assertEqual(len(django_mail.outbox), 1)
        mail = django_mail.outbox[0]

        self.assertIn(expected_subject, mail.subject)
        self.assertIn(appserver.name, mail.body)
        self.assertIn(appserver.instance.name, mail.body)
        self.assertIn(reason, mail.body)
        self.assertEqual(mail.from_email, settings.SERVER_EMAIL)
        self.assertEqual(mail.to, expected_recipients)

        self.assertEqual(len(mail.attachments), 2)
        self.assertEqual(mail.attachments[0], ("provision.log", "\n".join(log_lines), "text/plain"))
        name, content, mime_type = mail.attachments[1]
        self.assertEqual(name, "debug.html")
        self.assertIn(exception_message, content)
        self.assertEqual(mime_type, "text/html")

    @responses.activate
    @patch('instance.models.server.OpenStackServer.public_ip', new_callable=PropertyMock)
    def test_heartbeat_active_succeeds(self, mock_public_ip, mock_consul):
        """ Test that heartbeat_active method returns true when request to heartbeat is 200"""
        appserver = make_test_appserver()
        mock_public_ip.return_value = "1.1.1.1"

        responses.add(responses.OPTIONS, 'http://{}/heartbeat'.format(appserver.server.public_ip), status=200)
        self.assertTrue(appserver.heartbeat_active())

    @patch('requests.options')
    def test_heartbeat_active_fails(self, mock_requests_options, mock_consul):
        """ Test that heartbeat_active method returns false when request to heartbeat fails"""
        mock_requests_options.side_effect = requests.exceptions.ConnectionError()
        appserver = make_test_appserver()
        self.assertFalse(appserver.heartbeat_active())


class SiteConfigurationSettingsTestCase(TestCase):
    """
    Tests for configuration_site_configuration_setings.
    """
    def test_configuration_site_configuration_settings(self):
        """
        Test that the 'configuration_site_configuration_settings' field has the correct value set when
        there are static content overrides.
        """
        instance = OpenEdXInstanceFactory()
        instance.static_content_overrides = {
            'version': 0,
            'static_template_about_content': 'Hello world!',
            'homepage_overlay_html': 'Welcome to the LMS!',
        }
        instance.save()
        appserver = make_test_appserver(instance)
        expected_values = {
            'EDXAPP_SITE_CONFIGURATION': [
                {
                    'values': {
                        'static_template_about_content': 'Hello world!',
                        'homepage_overlay_html': 'Welcome to the LMS!',
                    }
                }
            ]
        }
        self.assertEqual(yaml.safe_load(appserver.configuration_site_configuration_settings), expected_values)
