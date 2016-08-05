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
OpenEdXAppServer model - Tests
"""

# Imports #####################################################################

from unittest.mock import patch, Mock

from ddt import ddt, data
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail as django_mail
from django.test import override_settings
import novaclient
import yaml

from instance.models.appserver import Status as AppServerStatus
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.server import Server
from instance.models.utils import WrongStateException
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

class OpenEdXAppServerTestCase(TestCase):
    """
    Test cases for OpenEdXAppServer objects
    """
    @patch_services
    def test_provision(self, mocks):
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
    def test_provision_build_failed(self, mocks):
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
    def test_provision_failed(self, mocks):
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
    def test_provision_unhandled_exception(self, mocks):
        """
        Make sure that if there is an unhandled exception during provisioning, the provision()
        method should return False and send an email.
        """
        mocks.mock_run_ansible_playbooks.side_effect = Exception('Something went catastrophically wrong')
        appserver = make_test_appserver()
        result = appserver.provision()
        self.assertFalse(result)
        mocks.mock_provision_failed_email.assert_called_once_with("AppServer deploy failed: unhandled exception")

    def test_github_admin_username_list_default(self):
        """
        By default, no admin should be configured
        """
        appserver = make_test_appserver()
        self.assertEqual(appserver.github_admin_organization_name, '')
        self.assertEqual(appserver.github_admin_username_list, [])
        self.assertNotIn('COMMON_USER_INFO', appserver.configuration_settings)

    @patch('instance.models.openedx_appserver.get_username_list_from_team')
    def test_github_admin_username_list_with_org_set(self, mock_get_username_list):
        """
        When an admin org is set, its members should be included in the ansible conf
        """
        mock_get_username_list.return_value = ['admin1', 'admin2']
        instance = OpenEdXInstanceFactory(github_admin_organization_name='test-admin-org')
        appserver = make_test_appserver(instance)
        self.assertEqual(appserver.github_admin_username_list, ['admin1', 'admin2'])
        ansible_settings = yaml.load(appserver.configuration_settings)
        self.assertEqual(ansible_settings['COMMON_USER_INFO'], [
            {'name': 'admin1', 'github': True, 'type': 'admin'},
            {'name': 'admin2', 'github': True, 'type': 'admin'},
        ])

    @patch_services
    def test_cannot_reprovision(self, mocks):
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

    def test_configuration_extra_settings(self):
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

    def test_lms_user_settings(self):
        """
        Test that lms_user_settings are initialised correctly for new AppServers.
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=True)
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        instance.lms_users.add(user)
        appserver = make_test_appserver(instance)
        ansible_settings = yaml.load(appserver.lms_user_settings)
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
    def test_postfix_queue_settings_present(self):
        """
        Check that ansible vars for postfix_queue role are set correctly.
        """
        instance = OpenEdXInstanceFactory(
            sub_domain='test.postfix.queue',
            use_ephemeral_databases=True,
            email='test.postfix@myinstance.org',
            external_lms_domain='lms.myinstance.org'
        )
        appserver = make_test_appserver(instance)
        configuration_vars = yaml.load(appserver.configuration_settings)
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_EXTERNAL_SMTP_HOST'], 'smtp.myhost.com')
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_EXTERNAL_SMTP_PORT'], '2525')
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_EXTERNAL_SMTP_USER'], 'smtpuser')
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_EXTERNAL_SMTP_PASSWORD'], 'smtppass')
        self.assertEqual(configuration_vars['POSTFIX_QUEUE_HEADER_CHECKS'], '/^From:(.*)$/   PREPEND Reply-To:$1')
        self.assertEqual(
            configuration_vars['POSTFIX_QUEUE_SENDER_CANONICAL_MAPS'],
            'test.postfix@myinstance.org  lms.myinstance.org@opencraft.hosting'
        )

    @override_settings(INSTANCE_SMTP_RELAY_HOST=None)
    def test_postfix_queue_settings_absent(self):
        """
        Check that ansible vars for postfix_queue role are not present when SMTP relay host is not configured.
        """
        instance = OpenEdXInstanceFactory(sub_domain='test.no.postfix.queue', use_ephemeral_databases=True)
        appserver = make_test_appserver(instance)
        configuration_vars = yaml.load(appserver.configuration_settings)
        self.assertNotIn('POSTFIX_QUEUE_EXTERNAL_SMTP_HOST', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_EXTERNAL_SMTP_PORT', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_EXTERNAL_SMTP_USER', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_EXTERNAL_SMTP_PASSWORD', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_HEADER_CHECKS', configuration_vars)
        self.assertNotIn('POSTFIX_QUEUE_SENDER_CANONICAL_MAPS', configuration_vars)


@ddt
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

    def test_status_transitions(self):
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
    def test_invalid_status_transitions(self, transition):
        """
        Test that invalid status transitions raise exception
        """
        # TODO: Get pylint to see state as an iterable
        invalid_from_states = (state for state in AppServerStatus.states #pylint: disable=not-an-iterable
                               if state not in transition['from_states'])
        for invalid_from_state in invalid_from_states:
            appserver = make_test_appserver()
            # Hack to force the status:
            OpenEdXAppServer.objects.filter(pk=appserver.pk).update(_status=invalid_from_state.state_id)
            appserver = OpenEdXAppServer.objects.get(pk=appserver.pk)
            self.assertEqual(appserver.status, invalid_from_state)
            with self.assertRaises(WrongStateException):
                getattr(appserver, transition['name'])()


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
    def test_provision_failed_email(self):
        """
        Tests that provision_failed sends email when called from normal program flow
        """
        appserver = make_test_appserver()
        reason = "something went wrong"
        log_lines = ["log line1", "log_line2"]

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

        self.assertEqual(len(mail.attachments), 1)
        self.assertEqual(mail.attachments[0], ("provision.log", "\n".join(log_lines), "text/plain"))

    @override_settings(ADMINS=(
        ("admin1", "admin1@localhost"),
        ("admin2", "admin2@localhost"),
    ))
    def test_provision_failed_exception_email(self):
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
