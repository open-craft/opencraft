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
Model Mixins - Tests
"""

# Imports #####################################################################

import os
import subprocess
from unittest.mock import patch, call

import pymongo
from django.conf import settings
from django.core import mail as django_mail
from django.test.utils import override_settings

from instance.models.instance import SingleVMOpenEdXInstance
from instance.tests.base import TestCase
from instance.tests.models.factories.instance import SingleVMOpenEdXInstanceFactory
from instance.tests.models.factories.server import (
    patch_os_server, BuildingOpenStackServerFactory,
    BootingOpenStackServerFactory, OpenStackServerFactory, ReadyOpenStackServerFactory
)


# Tests #######################################################################

#pylint: disable=no-member

class GitHubInstanceTestCase(TestCase):
    """
    Test cases for GitHubInstanceMixin models
    """
    def test_github_attributes(self):
        """
        GitHub-specific instance attributes
        """
        instance = SingleVMOpenEdXInstanceFactory(
            github_organization_name='open-craft',
            github_pr_url='https://github.com/edx/edx/pull/234',
            github_repository_name='edx',
            branch_name='test-branch',
        )
        self.assertEqual(instance.fork_name, 'open-craft/edx')
        self.assertEqual(instance.github_base_url, 'https://github.com/open-craft/edx')
        self.assertEqual(instance.github_pr_number, 234)
        self.assertEqual(instance.github_branch_url, 'https://github.com/open-craft/edx/tree/test-branch')
        self.assertEqual(instance.repository_url, 'https://github.com/open-craft/edx.git')
        self.assertEqual(instance.updates_feed, 'https://github.com/open-craft/edx/commits/test-branch.atom')

    def test_github_admin_username_list_default(self):
        """
        By default, no admin should be configured
        """
        instance = SingleVMOpenEdXInstanceFactory()
        instance.reset_ansible_settings()
        self.assertEqual(instance.github_admin_organization_name, '')
        self.assertEqual(instance.github_admin_username_list, [])
        self.assertNotIn('COMMON_USER_INFO', instance.ansible_settings)

    @patch('instance.models.mixins.version_control.get_username_list_from_team')
    def test_github_admin_username_list_with_org_set(self, mock_get_username_list):
        """
        When an admin org is set, its members should be included in the ansible conf
        """
        mock_get_username_list.return_value = ['admin1', 'admin2']
        instance = SingleVMOpenEdXInstanceFactory(github_admin_organization_name='test-admin-org')
        instance.reset_ansible_settings()
        self.assertEqual(instance.github_admin_username_list, ['admin1', 'admin2'])
        self.assertIn('COMMON_USER_INFO:\n  - name: admin1\n    github: true\n    type: admin\n'
                      '  - name: admin2\n    github: true\n    type: admin', instance.ansible_settings)

    def test_set_fork_name_commit(self):
        """
        Set org & repo using the fork name - Using the default commit policy (True)
        """
        instance = SingleVMOpenEdXInstanceFactory()
        instance.set_fork_name('org2/another-repo')
        self.assertEqual(instance.github_organization_name, 'org2')
        self.assertEqual(instance.github_repository_name, 'another-repo')

        # Check values in DB
        db_instance = SingleVMOpenEdXInstance.objects.get(pk=instance.pk)
        self.assertEqual(db_instance.github_organization_name, 'org2')
        self.assertEqual(db_instance.github_repository_name, 'another-repo')

    def test_set_fork_name_no_commit(self):
        """
        Set org & repo using the fork name, with commit=False
        """
        instance = SingleVMOpenEdXInstanceFactory(
            github_organization_name='open-craft',
            github_repository_name='edx',
        )
        instance.set_fork_name('org2/another-repo', commit=False)
        self.assertEqual(instance.github_organization_name, 'org2')
        self.assertEqual(instance.github_repository_name, 'another-repo')

        # Check values in DB
        db_instance = SingleVMOpenEdXInstance.objects.get(pk=instance.pk)
        self.assertEqual(db_instance.github_organization_name, 'open-craft')
        self.assertEqual(db_instance.github_repository_name, 'edx')

    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    def test_set_to_branch_tip_commit(self, mock_get_commit_id_from_ref):
        """
        Set the commit id to the tip of the current branch, using the default commit policy (True)
        """
        mock_get_commit_id_from_ref.return_value = 'b' * 40
        instance = SingleVMOpenEdXInstanceFactory(
            github_organization_name='org3',
            github_repository_name='repo3',
            commit_id='a' * 40,
        )
        instance.set_to_branch_tip()
        self.assertEqual(instance.commit_id, 'b' * 40)
        self.assertEqual(mock_get_commit_id_from_ref.mock_calls, [
            call('org3/repo3', 'master', ref_type='heads'),
        ])

        # Check values in DB
        db_instance = SingleVMOpenEdXInstance.objects.get(pk=instance.pk)
        self.assertEqual(db_instance.commit_id, 'b' * 40)

    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    def test_set_to_branch_tip_no_commit(self, mock_get_commit_id_from_ref):
        """
        Set the commit id to the tip of the current branch, with commit=False
        """
        mock_get_commit_id_from_ref.return_value = 'b' * 40
        instance = SingleVMOpenEdXInstanceFactory(commit_id='a' * 40)
        instance.set_to_branch_tip(commit=False)
        self.assertEqual(instance.commit_id, 'b' * 40)

        # Check values in DB
        db_instance = SingleVMOpenEdXInstance.objects.get(pk=instance.pk)
        self.assertEqual(db_instance.commit_id, 'a' * 40)

    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    def test_set_to_branch_tip_extra_args(self, mock_get_commit_id_from_ref):
        """
        Set the commit id to the tip of a specified reference
        """
        mock_get_commit_id_from_ref.return_value = 'c' * 40
        instance = SingleVMOpenEdXInstanceFactory(commit_id='a' * 40)
        instance.set_to_branch_tip(branch_name='new-branch', ref_type='tag')
        self.assertEqual(instance.commit_id, 'c' * 40)
        self.assertEqual(instance.branch_name, 'new-branch')
        self.assertEqual(instance.ref_type, 'tag')

    @patch('instance.models.mixins.version_control.github.get_commit_id_from_ref')
    def test_set_to_branch_tip_replace_commit_hash(self, mock_get_commit_id_from_ref):
        """
        The hash should be updated in the instance name when updating
        """
        mock_get_commit_id_from_ref.return_value = '1234567' + 'd' * 33
        instance = SingleVMOpenEdXInstanceFactory(commit_id='a' * 40, name='Test Instance (aaaaaaa)')
        instance.set_to_branch_tip(branch_name='new-branch', ref_type='tag')
        self.assertEqual(instance.name, 'Test Instance (1234567)')


class AnsibleInstanceTestCase(TestCase):
    """
    Test cases for AnsibleInstanceMixin models
    """
    def check_ansible_settings(self, instance, expected=True):
        """
        Verify the Ansible settings.
        """
        instance.reset_ansible_settings()
        expected_settings = {
            'EDXAPP_SWIFT_USERNAME': 'swift_openstack_user',
            'EDXAPP_SWIFT_KEY': 'swift_openstack_password',
            'EDXAPP_SWIFT_TENANT_NAME': 'swift_openstack_tenant',
            'EDXAPP_SWIFT_AUTH_URL': 'swift_openstack_auth_url',
            'EDXAPP_SWIFT_REGION_NAME': 'swift_openstack_region',
        }
        for ansible_var, attribute in expected_settings.items():
            if expected:
                self.assertIn('{}: {}'.format(ansible_var, getattr(instance, attribute)), instance.ansible_settings)
            else:
                self.assertNotIn(ansible_var, instance.ansible_settings)

    def test_ansible_playbook_filename(self):
        """
        Set name of ansible playbook & get filename
        """
        instance = SingleVMOpenEdXInstanceFactory(ansible_playbook_name='test_playbook')
        self.assertEqual(instance.ansible_playbook_filename, 'test_playbook.yml')

    @patch_os_server
    def test_inventory_str(self, os_server_manager):
        """
        Ansible inventory - showing servers once they are in ready status
        """
        instance = SingleVMOpenEdXInstanceFactory()
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 0: 'pending'
        OpenStackServerFactory(instance=instance)
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 1: 'building'
        BuildingOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 2: 'failed'
        server2 = BuildingOpenStackServerFactory(instance=instance)
        server2._status_to_build_failed()
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 3: 'booting'
        server3 = BootingOpenStackServerFactory(instance=instance)
        os_server_manager.add_fixture(server3.openstack_id, 'openstack/api_server_2_active.json')
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 4: 'terminated'
        server4 = ReadyOpenStackServerFactory(instance=instance)
        server4._status_to_terminated()
        os_server_manager.add_fixture(server4.openstack_id, 'openstack/api_server_2_active.json')
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 5: 'ready'
        server5 = ReadyOpenStackServerFactory(instance=instance)
        os_server_manager.add_fixture(server5.openstack_id, 'openstack/api_server_2_active.json')
        self.assertEqual(instance.inventory_str, '[app]\n192.168.100.200')

        # Server 6: 'ready'
        server6 = ReadyOpenStackServerFactory(instance=instance)
        os_server_manager.add_fixture(server6.openstack_id, 'openstack/api_server_3_active.json')
        self.assertEqual(instance.inventory_str, '[app]\n192.168.100.200\n192.168.99.66')

    def test_reset_ansible_settings(self):
        """
        Ansible vars as a string
        """
        instance = SingleVMOpenEdXInstanceFactory(
            name='Vars Instance',
            sub_domain='vars.test',
            email='vars@example.com',
            github_organization_name='vars-org',
            github_repository_name='vars-repo',
            commit_id='9' * 40,
            ansible_source_repo_url='http://example.org/config/repo',
            configuration_version='test-config-ver',
            forum_version='test-forum-ver',
            notifier_version='test-notif-ver',
            xqueue_version='test-xq-ver',
            certs_version='test-cert-ver',
        )
        instance.reset_ansible_settings()
        self.assertIn('EDXAPP_PLATFORM_NAME: "Vars Instance"', instance.ansible_settings)
        self.assertIn("EDXAPP_SITE_NAME: 'vars.test.example.com", instance.ansible_settings)
        self.assertIn("EDXAPP_CMS_SITE_NAME: 'studio.vars.test.example.com'", instance.ansible_settings)
        self.assertIn("EDXAPP_CONTACT_EMAIL: 'vars@example.com'", instance.ansible_settings)
        self.assertIn("edx_platform_repo: 'https://github.com/vars-org/vars-repo.git'", instance.ansible_settings)
        self.assertIn("edx_platform_version: '{}'".format('9' * 40), instance.ansible_settings)
        self.assertIn("edx_ansible_source_repo: 'http://example.org/config/repo'", instance.ansible_settings)
        self.assertIn("configuration_version: 'test-config-ver'", instance.ansible_settings)
        self.assertIn("forum_version: 'test-forum-ver'", instance.ansible_settings)
        self.assertIn("notifier_version: 'test-notif-ver'", instance.ansible_settings)
        self.assertIn("xqueue_version: 'test-xq-ver'", instance.ansible_settings)
        self.assertIn("certs_version: 'test-cert-ver'", instance.ansible_settings)

    def test_ansible_extra_settings(self):
        """
        Add extra settings in ansible vars, which can override existing settings
        """
        instance = SingleVMOpenEdXInstanceFactory(
            name='Vars Instance',
            email='vars@example.com',
            ansible_extra_settings='EDXAPP_PLATFORM_NAME: "Overriden!"',
        )
        instance.reset_ansible_settings()
        self.assertIn('EDXAPP_PLATFORM_NAME: Overriden!', instance.ansible_settings)
        self.assertNotIn('Vars Instance', instance.ansible_settings)
        self.assertIn("EDXAPP_CONTACT_EMAIL: vars@example.com", instance.ansible_settings)

    @patch('instance.models.mixins.ansible.poll_streams')
    @patch('instance.models.instance.SingleVMOpenEdXInstance.inventory_str')
    @patch('instance.models.mixins.ansible.ansible.run_playbook')
    @patch('instance.models.mixins.ansible.open_repository')
    def test_deployment(self, mock_open_repo, mock_run_playbook, mock_inventory, mock_poll_streams):
        """
        Test instance deployment
        """
        instance = SingleVMOpenEdXInstanceFactory()
        ReadyOpenStackServerFactory(instance=instance)
        mock_open_repo.return_value.__enter__.return_value.working_dir = '/cloned/configuration-repo/path'

        instance.deploy()
        self.assertIn(call(
            '/cloned/configuration-repo/path/requirements.txt',
            mock_inventory,
            instance.ansible_settings,
            '/cloned/configuration-repo/path/playbooks',
            'edx_sandbox.yml',
            username='ubuntu',
        ), mock_run_playbook.mock_calls)

    @patch('instance.models.mixins.ansible.ansible.run_playbook')
    def test_run_playbook_logging(self, mock_run_playbook):
        """
        Ensure logging routines are working on _run_playbook method
        """
        stdout_r, stdout_w = os.pipe()
        stderr_r, stderr_w = os.pipe()
        with open(stdout_r, 'rb', buffering=0) as stdout, open(stderr_r, 'rb', buffering=0) as stderr:
            mock_run_playbook.return_value.__enter__.return_value.stdout = stdout
            mock_run_playbook.return_value.__enter__.return_value.stderr = stderr
            mock_run_playbook.return_value.__enter__.return_value.returncode = 0
            os.write(stdout_w, b'Hello\n')
            os.close(stdout_w)
            os.write(stderr_w, b'Hi\n')
            os.close(stderr_w)
            instance = SingleVMOpenEdXInstanceFactory()
            log, returncode = instance._run_playbook("requirements", "playbook")
            self.assertCountEqual(log, ['Hello', 'Hi'])
            self.assertEqual(returncode, 0)

    def test_ansible_settings_swift(self):
        """
        Verify Swift Ansible configuration when Swift is enabled.
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.check_ansible_settings(instance)

    @override_settings(SWIFT_ENABLE=False)
    def test_ansible_settings_swift_disabled(self):
        """
        Verify Swift Ansible configuration is not included when Swift is disabled.
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.check_ansible_settings(instance, expected=False)

    def test_ansible_settings_swift_ephemeral(self):
        """
        Verify Swift Ansible configuration is not included when using ephemeral databases.
        """
        instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=True)
        self.check_ansible_settings(instance, expected=False)


class MySQLInstanceTestCase(TestCase):
    """
    Test cases for MySQLInstanceMixin models
    """
    def setUp(self):
        super().setUp()
        self.instance = None

    def tearDown(self):
        if self.instance:
            self.instance.deprovision_mysql()
        super().tearDown()

    def check_mysql(self):
        """
        Check that the mysql databases and user have been created, then remove them
        """
        self.assertIs(self.instance.mysql_provisioned, True)
        self.assertTrue(self.instance.mysql_user)
        self.assertTrue(self.instance.mysql_pass)
        databases = subprocess.check_output("mysql -u root -e 'SHOW DATABASES'", shell=True).decode()
        for database in self.instance.mysql_database_names:
            self.assertIn(database, databases)
            # Pass password using MYSQ_PWD environment variable rather than the --password
            # parameter so that mysql command doesn't print a security warning.
            mysql_cmd = "MYSQL_PWD={password} mysql -u {user} -e 'SHOW TABLES' {db_name}".format(
                password=self.instance.mysql_pass,
                user=self.instance.mysql_user,
                db_name=database,
            )
            tables = subprocess.call(mysql_cmd, shell=True)
            self.assertEqual(tables, 0)

    def test_provision_mysql(self):
        """
        Provision mysql database
        """
        self.instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mysql()
        self.check_mysql()

    @override_settings(INSTANCE_MYSQL_URL_OBJ=None)
    def test_provision_mysql_no_url(self):
        """
        Don't provision a mysql database if INSTANCE_MYSQL_URL is not set
        """
        self.instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mysql()
        databases = subprocess.check_output("mysql -u root -e 'SHOW DATABASES'", shell=True).decode()
        for database in self.instance.mysql_database_names:
            self.assertNotIn(database, databases)

    def test_provision_mysql_weird_domain(self):
        """
        Make sure that database names are escaped correctly
        """
        sub_domain = 'really.really.really.really.long.subdomain'
        base_domain = 'this-is-a-really-long-unusual-domain-แปลกมาก.com'
        self.instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False,
                                                       sub_domain=sub_domain,
                                                       base_domain=base_domain)
        self.instance.provision_mysql()
        self.check_mysql()

    def test_provision_mysql_again(self):
        """
        Only create the database once
        """
        self.instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mysql()
        self.assertIs(self.instance.mysql_provisioned, True)

        mysql_user = self.instance.mysql_user
        mysql_pass = self.instance.mysql_pass
        self.instance.provision_mysql()
        self.assertEqual(self.instance.mysql_user, mysql_user)
        self.assertEqual(self.instance.mysql_pass, mysql_pass)
        self.check_mysql()


class MongoDBInstanceTestCase(TestCase):
    """
    Test cases for MongoDBInstanceMixin models
    """
    def setUp(self):
        super().setUp()
        self.instance = None

    def tearDown(self):
        if self.instance:
            self.instance.deprovision_mongo()
        super().tearDown()

    def check_mongo(self):
        """
        Check that the instance mongo user has access to the external mongo database
        """
        mongo = pymongo.MongoClient(settings.INSTANCE_MONGO_URL)
        for database in self.instance.mongo_database_names:
            self.assertTrue(mongo[database].authenticate(self.instance.mongo_user, self.instance.mongo_pass))

    def test_provision_mongo(self):
        """
        Provision mongo databases
        """
        self.instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mongo()
        self.check_mongo()

    def test_provision_mongo_no_url(self):
        """
        Don't provision any mongo databases if INSTANCE_MONGO_URL is not set
        """
        mongo = pymongo.MongoClient(settings.INSTANCE_MONGO_URL)
        with override_settings(INSTANCE_MONGO_URL=None):
            self.instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
            self.instance.provision_mongo()
            databases = mongo.database_names()
            for database in self.instance.mongo_database_names:
                self.assertNotIn(database, databases)

    def test_provision_mongo_again(self):
        """
        Only create the databases once
        """
        self.instance = SingleVMOpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mongo()
        self.assertIs(self.instance.mongo_provisioned, True)

        mongo_user = self.instance.mongo_user
        mongo_pass = self.instance.mongo_pass
        self.instance.provision_mongo()
        self.assertEqual(self.instance.mongo_user, mongo_user)
        self.assertEqual(self.instance.mongo_pass, mongo_pass)
        self.check_mongo()


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
        instance = SingleVMOpenEdXInstanceFactory(name='test', sub_domain='test')
        reason = "something went wrong"
        log_lines = ["log line1", "log_line2"]

        instance.provision_failed_email(reason, log_lines)

        expected_subject = SingleVMOpenEdXInstance.EmailSubject.PROVISION_FAILED.format(
            instance_name=instance.name, instance_url=instance.url
        )
        expected_recipients = [admin_tuple[1] for admin_tuple in settings.ADMINS]

        self.assertEqual(len(django_mail.outbox), 1)
        mail = django_mail.outbox[0]

        self.assertIn(expected_subject, mail.subject)
        self.assertIn(instance.name, mail.body)
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
        instance = SingleVMOpenEdXInstanceFactory(name='exception_test', sub_domain='exception_test')
        reason = "something went wrong"
        log_lines = ["log line1", "log_line2"]

        exception_message = "Something Bad happened Unexpectedly"
        exception = Exception(exception_message)
        try:
            raise exception
        except Exception:  # pylint: disable=broad-except
            instance.provision_failed_email(reason, log_lines)

        expected_subject = SingleVMOpenEdXInstance.EmailSubject.PROVISION_FAILED.format(
            instance_name=instance.name, instance_url=instance.url
        )
        expected_recipients = [admin_tuple[1] for admin_tuple in settings.ADMINS]

        self.assertEqual(len(django_mail.outbox), 1)
        mail = django_mail.outbox[0]

        self.assertIn(expected_subject, mail.subject)
        self.assertIn(instance.name, mail.body)
        self.assertIn(reason, mail.body)
        self.assertEqual(mail.from_email, settings.SERVER_EMAIL)
        self.assertEqual(mail.to, expected_recipients)

        self.assertEqual(len(mail.attachments), 2)
        self.assertEqual(mail.attachments[0], ("provision.log", "\n".join(log_lines), "text/plain"))
        name, content, mime_type = mail.attachments[1]
        self.assertEqual(name, "debug.html")
        self.assertIn(exception_message, content)
        self.assertEqual(mime_type, "text/html")
