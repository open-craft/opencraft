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
OpenEdXInstance model - Tests
"""

# Imports #####################################################################

import os
import re
from mock import call, patch
from urllib.parse import urlparse

from django.conf import settings
from django.test import override_settings

import MySQLdb as mysql
import pymongo
import yaml

from instance.models.server import OpenStackServer, Server
from instance.models.instance import InconsistentInstanceState, OpenEdXInstance
from instance.tests.base import TestCase
from instance.tests.factories.pr import PRFactory
from instance.tests.models.factories.instance import OpenEdXInstanceFactory
from instance.tests.models.factories.server import (
    StartedOpenStackServerFactory, BootedOpenStackServerFactory, ProvisioningOpenStackServerFactory,
    patch_os_server)


# Tests #######################################################################

# Factory boy doesn't properly support pylint+django
#pylint: disable=no-member,too-many-arguments

class InstanceTestCase(TestCase):
    """
    Test cases for instance models
    """
    def test_new_instance(self):
        """
        New OpenEdXInstance object
        """
        self.assertFalse(OpenEdXInstance.objects.all())
        instance = OpenEdXInstanceFactory()
        self.assertEqual(OpenEdXInstance.objects.get().pk, instance.pk)
        self.assertTrue(re.search(r'Test Instance \d+ \(http://instance\d+\.test\.example\.com/\)', str(instance)))

    def test_domain_url(self):
        """
        Domain and URL attributes
        """
        instance = OpenEdXInstanceFactory(base_domain='example.org', sub_domain='sample', name='Sample Instance')
        self.assertEqual(instance.domain, 'sample.example.org')
        self.assertEqual(instance.url, 'http://sample.example.org/')
        self.assertEqual(instance.studio_domain, 'studio.sample.example.org')
        self.assertEqual(instance.studio_url, 'http://studio.sample.example.org/')
        self.assertEqual(str(instance), 'Sample Instance (http://sample.example.org/)')

    def test_commit_short_id(self):
        """
        Short representation of a commit_id
        """
        instance = OpenEdXInstanceFactory(commit_id='6e580ca9fed6fb65ec45949494dabec40e8cb533')
        self.assertEqual(instance.commit_short_id, '6e580ca')
        instance.commit_id = None
        self.assertEqual(instance.commit_short_id, None)

    def test_status(self):
        """
        Instance status with one active server
        """
        instance = OpenEdXInstanceFactory()
        self.assertEqual(instance.status, instance.EMPTY)
        self.assertEqual(instance.progress, instance.EMPTY)
        server = StartedOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.status, instance.STARTED)
        self.assertEqual(instance.progress, instance.PROGRESS_RUNNING)
        server.status = server.BOOTED
        server.save()
        self.assertEqual(instance.status, instance.BOOTED)

    def test_status_terminated(self):
        """
        Instance status should revert to 'empty' when all its servers are terminated
        """
        instance = OpenEdXInstanceFactory()
        server = StartedOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.status, instance.STARTED)
        server.status = 'terminated'
        server.save()
        self.assertEqual(instance.status, instance.EMPTY)

    def test_status_multiple_servers(self):
        """
        Instance status should not allow multiple active servers
        """
        instance = OpenEdXInstanceFactory()
        StartedOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.status, instance.STARTED)
        self.assertEqual(instance.progress, instance.PROGRESS_RUNNING)
        StartedOpenStackServerFactory(instance=instance)
        with self.assertRaises(InconsistentInstanceState):
            instance.status #pylint: disable=pointless-statement


class GitHubInstanceTestCase(TestCase):
    """
    Test cases for GitHubInstanceMixin models
    """
    def test_github_attributes(self):
        """
        GitHub-specific instance attributes
        """
        instance = OpenEdXInstanceFactory(
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
        instance = OpenEdXInstanceFactory()
        instance.reset_ansible_settings()
        self.assertEqual(instance.github_admin_organization_name, '')
        self.assertEqual(instance.github_admin_username_list, [])
        self.assertNotIn('COMMON_USER_INFO', instance.ansible_settings)

    @patch('instance.models.instance.get_username_list_from_team')
    def test_github_admin_username_list_with_org_set(self, mock_get_username_list):
        """
        When an admin org is set, its members should be included in the ansible conf
        """
        mock_get_username_list.return_value = ['admin1', 'admin2']
        instance = OpenEdXInstanceFactory(github_admin_organization_name='test-admin-org')
        instance.reset_ansible_settings()
        self.assertEqual(instance.github_admin_username_list, ['admin1', 'admin2'])
        self.assertIn('COMMON_USER_INFO:\n  - name: admin1\n    github: true\n    type: admin\n'
                      '  - name: admin2\n    github: true\n    type: admin', instance.ansible_settings)

    def test_set_fork_name_commit(self):
        """
        Set org & repo using the fork name - Using the default commit policy (True)
        """
        instance = OpenEdXInstanceFactory()
        instance.set_fork_name('org2/another-repo')
        self.assertEqual(instance.github_organization_name, 'org2')
        self.assertEqual(instance.github_repository_name, 'another-repo')

        # Check values in DB
        db_instance = OpenEdXInstance.objects.get(pk=instance.pk)
        self.assertEqual(db_instance.github_organization_name, 'org2')
        self.assertEqual(db_instance.github_repository_name, 'another-repo')

    def test_set_fork_name_no_commit(self):
        """
        Set org & repo using the fork name, with commit=False
        """
        instance = OpenEdXInstanceFactory(
            github_organization_name='open-craft',
            github_repository_name='edx',
        )
        instance.set_fork_name('org2/another-repo', commit=False)
        self.assertEqual(instance.github_organization_name, 'org2')
        self.assertEqual(instance.github_repository_name, 'another-repo')

        # Check values in DB
        db_instance = OpenEdXInstance.objects.get(pk=instance.pk)
        self.assertEqual(db_instance.github_organization_name, 'open-craft')
        self.assertEqual(db_instance.github_repository_name, 'edx')

    @patch('instance.models.instance.github.get_commit_id_from_ref')
    def test_set_to_branch_tip_commit(self, mock_get_commit_id_from_ref):
        """
        Set the commit id to the tip of the current branch, using the default commit policy (True)
        """
        mock_get_commit_id_from_ref.return_value = 'b' * 40
        instance = OpenEdXInstanceFactory(
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
        db_instance = OpenEdXInstance.objects.get(pk=instance.pk)
        self.assertEqual(db_instance.commit_id, 'b' * 40)

    @patch('instance.models.instance.github.get_commit_id_from_ref')
    def test_set_to_branch_tip_no_commit(self, mock_get_commit_id_from_ref):
        """
        Set the commit id to the tip of the current branch, with commit=False
        """
        mock_get_commit_id_from_ref.return_value = 'b' * 40
        instance = OpenEdXInstanceFactory(commit_id='a' * 40)
        instance.set_to_branch_tip(commit=False)
        self.assertEqual(instance.commit_id, 'b' * 40)

        # Check values in DB
        db_instance = OpenEdXInstance.objects.get(pk=instance.pk)
        self.assertEqual(db_instance.commit_id, 'a' * 40)

    @patch('instance.models.instance.github.get_commit_id_from_ref')
    def test_set_to_branch_tip_extra_args(self, mock_get_commit_id_from_ref):
        """
        Set the commit id to the tip of a specified reference
        """
        mock_get_commit_id_from_ref.return_value = 'c' * 40
        instance = OpenEdXInstanceFactory(commit_id='a' * 40)
        instance.set_to_branch_tip(branch_name='new-branch', ref_type='tag')
        self.assertEqual(instance.commit_id, 'c' * 40)
        self.assertEqual(instance.branch_name, 'new-branch')
        self.assertEqual(instance.ref_type, 'tag')

    @patch('instance.models.instance.github.get_commit_id_from_ref')
    def test_set_to_branch_tip_replace_commit_hash(self, mock_get_commit_id_from_ref):
        """
        The hash should be updated in the instance name when updating
        """
        mock_get_commit_id_from_ref.return_value = '1234567' + 'd' * 33
        instance = OpenEdXInstanceFactory(commit_id='a' * 40, name='Test Instance (aaaaaaa)')
        instance.set_to_branch_tip(branch_name='new-branch', ref_type='tag')
        self.assertEqual(instance.name, 'Test Instance (1234567)')


class AnsibleInstanceTestCase(TestCase):
    """
    Test cases for AnsibleInstanceMixin models
    """
    def test_ansible_playbook_filename(self):
        """
        Set name of ansible playbook & get filename
        """
        instance = OpenEdXInstanceFactory(ansible_playbook_name='test_playbook')
        self.assertEqual(instance.ansible_playbook_filename, 'test_playbook.yml')

    @patch_os_server
    def test_inventory_str(self, os_server_manager):
        """
        Ansible inventory - showing servers once they are in booted status
        """
        instance = OpenEdXInstanceFactory()
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 1: 'started'
        StartedOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 2: 'booted'
        server2 = BootedOpenStackServerFactory(instance=instance)
        os_server_manager.add_fixture(server2.openstack_id, 'openstack/api_server_2_active.json')
        self.assertEqual(instance.inventory_str, '[app]')

        # Server 3: 'provisioning'
        server3 = ProvisioningOpenStackServerFactory(instance=instance)
        os_server_manager.add_fixture(server3.openstack_id, 'openstack/api_server_2_active.json')
        self.assertEqual(instance.inventory_str, '[app]\n192.168.100.200')

        # Server 4: 'provisioning'
        server4 = ProvisioningOpenStackServerFactory(instance=instance)
        os_server_manager.add_fixture(server4.openstack_id, 'openstack/api_server_3_active.json')
        self.assertEqual(instance.inventory_str, '[app]\n192.168.100.200\n192.168.99.66')

    def test_reset_ansible_settings(self):
        """
        Ansible vars as a string
        """
        instance = OpenEdXInstanceFactory(
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
        instance = OpenEdXInstanceFactory(
            name='Vars Instance',
            email='vars@example.com',
            ansible_extra_settings='EDXAPP_PLATFORM_NAME: "Overriden!"',
        )
        instance.reset_ansible_settings()
        self.assertIn('EDXAPP_PLATFORM_NAME: Overriden!', instance.ansible_settings)
        self.assertNotIn('Vars Instance', instance.ansible_settings)
        self.assertIn("EDXAPP_CONTACT_EMAIL: vars@example.com", instance.ansible_settings)

    @patch('instance.models.instance.poll_streams')
    @patch('instance.models.instance.OpenEdXInstance.inventory_str')
    @patch('instance.models.instance.ansible.run_playbook')
    @patch('instance.models.instance.open_repository')
    def test_deployment(self, mock_open_repo, mock_run_playbook, mock_inventory, mock_poll_streams):
        """
        Test instance deployment
        """
        instance = OpenEdXInstanceFactory()
        BootedOpenStackServerFactory(instance=instance)
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

    @patch('instance.models.instance.ansible.run_playbook')
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
            instance = OpenEdXInstanceFactory()
            log, returncode = instance._run_playbook("requirements", "playbook")
            self.assertCountEqual(log, ['Hello', 'Hi'])
            self.assertEqual(returncode, 0)


class MySQLInstanceTestCase(TestCase):
    """
    Test cases for MySQLInstanceMixin models
    """
    def check_mysql(self, instance):
        """
        Check that the mysql databases and user have been created, and that we can write utf-8 data
        to them. Then remove the databases and user.
        """
        self.assertIs(instance.mysql_provisioned, True)
        self.assertTrue(instance.mysql_user)
        self.assertTrue(instance.mysql_pass)

        databases = self.show_databases()
        try:
            for database in instance.mysql_database_names:
                self.assertIn(database, databases)
                self.check_database(database,
                                    username=instance.mysql_user,
                                    password=instance.mysql_pass)
        finally:
            connection = mysql.connect(user='root')
            cursor = connection.cursor()
            for database in instance.mysql_database_names:
                #pylint: disable=undefined-loop-variable
                cursor.execute('DROP DATABASE IF EXISTS {0}'.format(database))
            cursor.execute('DROP USER {0}'.format(instance.mysql_user))
            connection.close()

    @staticmethod
    def show_databases():
        """
        Return a list of mysql databases
        """
        connection = mysql.connect(user='root')
        cursor = connection.cursor()
        cursor.execute('SHOW DATABASES')
        try:
            return [row[0] for row in cursor.fetchall()]
        finally:
            connection.close()

    def check_database(self, database, username, password):
        """
        Check that the given credentials have read/write access to the given database, and that the
        database can handle utf-8 data.
        """
        connection = mysql.connect(host='localhost',
                                   user=username,
                                   passwd=password,
                                   db=database,
                                   charset='utf8mb4')
        cursor = connection.cursor()
        test_sql = ("CREATE TABLE test (value TEXT)",
                    "INSERT INTO test (value) VALUES ('OHAI 😜')",
                    "SELECT value FROM test")
        try:
            for sql in test_sql:
                cursor.execute(sql)
            result = cursor.fetchone()[0]
            self.assertIn('😜', result)
        finally:
            connection.close()

    def test_provision_mysql(self):
        """
        Provision mysql database
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_mysql()
        self.check_mysql(instance)

    @override_settings(INSTANCE_MYSQL_URL_OBJ=None)
    def test_provision_mysql_no_url(self):
        """
        Don't provision a mysql database if INSTANCE_MYSQL_URL is not set
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_mysql()
        databases = self.show_databases()
        for database in instance.mysql_database_names:
            self.assertNotIn(database, databases)

    def test_provision_mysql_weird_domain(self):
        """
        Make sure that database names are escaped correctly
        """
        sub_domain = 'really.really.really.really.long.subdomain'
        base_domain = 'this-is-a-really-long-unusual-domain-แปลกมาก.com'
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False,
                                          sub_domain=sub_domain,
                                          base_domain=base_domain)
        instance.provision_mysql()
        self.check_mysql(instance)

    def test_provision_mysql_again(self):
        """
        Only create the database once
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_mysql()
        self.assertIs(instance.mysql_provisioned, True)

        mysql_user = instance.mysql_user
        mysql_pass = instance.mysql_pass
        instance.provision_mysql()
        self.assertEqual(instance.mysql_user, mysql_user)
        self.assertEqual(instance.mysql_pass, mysql_pass)
        self.check_mysql(instance)


class MongoDBInstanceTestCase(TestCase):
    """
    Test cases for MongoDBInstanceMixin models
    """
    def check_mongo(self, instance):
        """
        Check that the instance mongo user has access to the external mongo database
        """
        mongo = pymongo.MongoClient(settings.INSTANCE_MONGO_URL)
        for database in instance.mongo_database_names:
            self.assertTrue(mongo[database].authenticate(instance.mongo_user, instance.mongo_pass))
            mongo[database].remove_user(instance.mongo_user)

    def test_provision_mongo(self):
        """
        Provision mongo databases
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_mongo()
        self.check_mongo(instance)

    def test_provision_mongo_no_url(self):
        """
        Don't provision any mongo databases if INSTANCE_MONGO_URL is not set
        """
        mongo = pymongo.MongoClient(settings.INSTANCE_MONGO_URL)
        with override_settings(INSTANCE_MONGO_URL=None):
            instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
            instance.provision_mongo()
            databases = mongo.database_names()
            for database in instance.mongo_database_names:
                self.assertNotIn(database, databases)

    def test_provision_mongo_again(self):
        """
        Only create the databases once
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_mongo()
        self.assertIs(instance.mongo_provisioned, True)

        mongo_user = instance.mongo_user
        mongo_pass = instance.mongo_pass
        instance.provision_mongo()
        self.assertEqual(instance.mongo_user, mongo_user)
        self.assertEqual(instance.mongo_pass, mongo_pass)
        self.check_mongo(instance)


class OpenEdXInstanceTestCase(TestCase):
    """
    Test cases for OpenEdXInstanceMixin models
    """
    @override_settings(INSTANCE_EPHEMERAL_DATABASES=False)
    @patch('instance.models.instance.github.get_commit_id_from_ref')
    def test_create_defaults(self, mock_get_commit_id_from_ref):
        """
        Create an instance without specifying additional fields,
        leaving it up to the create method to set them
        """
        mock_get_commit_id_from_ref.return_value = '9' * 40
        instance = OpenEdXInstance.objects.create(sub_domain='create.defaults')
        self.assertEqual(instance.github_organization_name, 'edx')
        self.assertEqual(instance.github_repository_name, 'edx-platform')
        self.assertEqual(instance.commit_id, '9' * 40)
        self.assertEqual(instance.name, 'edx/master (9999999)')
        self.assertFalse(instance.mysql_user)
        self.assertFalse(instance.mysql_pass)
        self.assertFalse(instance.mongo_user)
        self.assertFalse(instance.mongo_pass)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=True)
    @patch('instance.models.instance.github.get_commit_id_from_ref')
    def test_create_from_pr(self, mock_get_commit_id_from_ref):
        """
        Create an instance from a pull request
        """
        mock_get_commit_id_from_ref.return_value = '9' * 40
        pr = PRFactory()
        instance, created = OpenEdXInstance.objects.update_or_create_from_pr(pr, sub_domain='test.sandbox')
        self.assertTrue(created)
        self.assertEqual(instance.fork_name, pr.fork_name)
        self.assertEqual(instance.branch_name, pr.branch_name)
        self.assertRegex(instance.name, r'^PR')
        self.assertEqual(instance.github_pr_number, pr.number)
        self.assertIs(instance.use_ephemeral_databases, True)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=False)
    @patch('instance.models.instance.github.get_commit_id_from_ref')
    def test_create_from_pr_ephemeral_databases(self, mock_get_commit_id_from_ref):
        """
        Instances should use ephemeral databases if requested in the PR
        """
        mock_get_commit_id_from_ref.return_value = '9' * 40
        pr = PRFactory(body='test.sandbox.example.com (ephemeral databases)')
        instance, _ = OpenEdXInstance.objects.update_or_create_from_pr(pr, sub_domain='test.sandbox')
        self.assertIs(instance.use_ephemeral_databases, True)

    @override_settings(INSTANCE_EPHEMERAL_DATABASES=True)
    @patch('instance.models.instance.github.get_commit_id_from_ref')
    def test_create_from_pr_persistent_databases(self, mock_get_commit_id_from_ref):
        """
        Instances should use persistent databases if requested in the PR
        """
        mock_get_commit_id_from_ref.return_value = '9' * 40
        pr = PRFactory(body='test.sandbox.example.com (persistent databases)')
        instance, _ = OpenEdXInstance.objects.update_or_create_from_pr(pr, sub_domain='test.sandbox')
        self.assertIs(instance.use_ephemeral_databases, False)

    def test_get_by_fork_name(self):
        """
        Use `fork_name` to get an instance object from the ORM
        """
        OpenEdXInstanceFactory(
            github_organization_name='get-by',
            github_repository_name='fork-name',
        )
        instance = OpenEdXInstance.objects.get(fork_name='get-by/fork-name')
        self.assertEqual(instance.fork_name, 'get-by/fork-name')

    def test_ansible_s3_settings(self):
        """
        Add extra settings in ansible vars, which can override existing settings
        """
        instance = OpenEdXInstanceFactory(
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
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
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
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.reset_ansible_settings()
        self.check_mysql_vars_not_set(instance)

    @override_settings(INSTANCE_MYSQL_URL_OBJ=urlparse('mysql://user:pass@mysql.opencraft.com'))
    def test_ansible_settings_mysql_ephemeral(self):
        """
        Don't add mysql ansible vars for ephemeral databases
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=True)
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
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
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
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.reset_ansible_settings()
        self.check_mongo_vars_not_set(instance)

    @override_settings(INSTANCE_MONGO_URL_OBJ=urlparse('mongodb://user:pass@mongo.opencraft.com'))
    def test_ansible_settings_mongo_ephemeral(self):
        """
        Don't add mongo ansible vars if INSTANCE_MONGO_URL is not set
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=True)
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

    @patch_os_server
    @patch('instance.models.server.openstack.create_server')
    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.OpenStackServer.sleep_until_status')
    @patch('instance.models.server.OpenStackServer.reboot')
    @patch('instance.models.instance.gandi.set_dns_record')
    @patch('instance.models.instance.OpenEdXInstance.deploy')
    @patch('instance.models.instance.OpenEdXInstance.provision_mysql')
    @patch('instance.models.instance.OpenEdXInstance.provision_mongo')
    def test_provision(self, os_server_manager, mock_provision_mongo, mock_provision_mysql, mock_deploy,
                       mock_set_dns_record, mock_server_reboot, mock_sleep_until_status, mock_update_status,
                       mock_openstack_create_server):
        """
        Run provisioning sequence
        """
        mock_deploy.return_value = (['log'], 0)
        mock_openstack_create_server.return_value.id = 'test-run-provisioning-server'
        os_server_manager.add_fixture('test-run-provisioning-server', 'openstack/api_server_2_active.json')

        instance = OpenEdXInstanceFactory(sub_domain='run.provisioning', use_ephemeral_databases=True)
        instance.provision()
        self.assertEqual(mock_set_dns_record.mock_calls, [
            call(name='run.provisioning', type='A', value='192.168.100.200'),
            call(name='studio.run.provisioning', type='CNAME', value='run.provisioning'),
        ])
        self.assertEqual(mock_deploy.call_count, 1)
        self.assertEqual(mock_server_reboot.call_count, 1)
        self.assertEqual(mock_provision_mysql.call_count, 0)
        self.assertEqual(mock_provision_mongo.call_count, 0)

    @patch_os_server
    @patch('instance.models.server.OpenStackServer.sleep_until_status')
    @patch('instance.models.server.OpenStackServer.os_server', autospec=True)
    @patch('instance.models.server.OpenStackServer.start', autospec=True)
    @patch('instance.models.instance.gandi.set_dns_record')
    @patch('instance.models.instance.OpenEdXInstance.deploy')
    def test_provision_failed(self, os_server_manager, mock_deploy, mock_set_dns_record,
                              mock_server_start, mock_os_server, mock_sleep_until_status):
        """
        Run provisioning sequence failing the deployment on purpose to make sure the
        server status will be set accordingly.
        """
        mock_deploy.return_value = (['log'], 1)
        instance = OpenEdXInstanceFactory(sub_domain='run.provisioning')

        def server_start(self):
            """
            Make sure we get the server in the BOOTED state when it is started
            """
            self.status = Server.BOOTED
            self.progress = Server.PROGRESS_SUCCESS
        mock_server_start.side_effect = server_start

        server = instance.provision()[0]
        self.assertEqual(server.status, Server.PROVISIONING)
        self.assertEqual(server.progress, Server.PROGRESS_FAILED)

    @patch_os_server
    @patch('instance.models.server.OpenStackServer.update_status', autospec=True)
    @patch('instance.models.server.time.sleep')
    @patch('instance.models.server.OpenStackServer.reboot')
    @patch('instance.models.instance.gandi.set_dns_record')
    @patch('instance.models.instance.OpenEdXInstance.deploy')
    @patch('instance.models.instance.OpenEdXInstance.provision_mysql')
    @patch('instance.models.instance.OpenEdXInstance.provision_mongo')
    def test_provision_no_active(self, os_server_manager, mock_provision_mongo, mock_provision_mysql, mock_deploy,
                                 mock_set_dns_record, mock_server_reboot, mock_sleep, mock_update_status):
        """
        Run provisioning sequence, with status jumping from 'started' to 'booted' (no 'active')
        """
        mock_deploy.return_value = (['log'], 0)
        instance = OpenEdXInstanceFactory(sub_domain='run.provisioning.noactive')
        status_queue = [
            OpenStackServer.STARTED,
            OpenStackServer.BOOTED,
            OpenStackServer.BOOTED,
            OpenStackServer.PROVISIONING,
            OpenStackServer.REBOOTING,
            OpenStackServer.READY,
        ]
        status_queue.reverse() # To be able to use pop()

        def update_status(self, provisioning=False, rebooting=False, failed=None):
            """ Simulate status progression successive runs """
            self.status = status_queue.pop()
            self.progress = self.PROGRESS_SUCCESS
        mock_update_status.side_effect = update_status

        with patch('instance.models.server.OpenStackServer.start'):
            instance.provision()
        self.assertEqual(mock_deploy.call_count, 1)

    @patch_os_server
    @patch('instance.models.server.openstack.create_server')
    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.OpenStackServer.sleep_until_status')
    @patch('instance.models.server.OpenStackServer.reboot')
    @patch('instance.models.instance.gandi.set_dns_record')
    @patch('instance.models.instance.OpenEdXInstance.deploy')
    @patch('instance.models.instance.MySQLInstanceMixin.provision_mysql')
    @patch('instance.models.instance.MongoDBInstanceMixin.provision_mongo')
    def test_provision_with_external_databases(self, os_server_manager, mock_provision_mongo, mock_provision_mysql,
                                               mock_deploy, mock_set_dns_record, mock_server_reboot,
                                               mock_sleep_until_status, mock_update_status,
                                               mock_openstack_create_server):
        """
        Run provisioning sequence, with external databases
        """
        mock_openstack_create_server.return_value.id = 'test-run-provisioning-server'
        os_server_manager.add_fixture('test-run-provisioning-server', 'openstack/api_server_2_active.json')

        instance = OpenEdXInstanceFactory(sub_domain='run.provisioning', use_ephemeral_databases=False)

        def deploy():
            """
            Make sure that ansible settings are present at deploy time
            """
            ansible_settings = yaml.load(instance.ansible_settings)
            for setting in ('EDXAPP_MYSQL_USER', 'EDXAPP_MONGO_PASSWORD',
                            'EDXAPP_MONGO_USER', 'EDXAPP_MONGO_PASSWORD'):
                self.assertTrue(ansible_settings[setting])
            return (['log'], 0)

        mock_deploy.side_effect = deploy
        instance.provision()
        self.assertEqual(mock_provision_mysql.call_count, 1)
        self.assertEqual(mock_provision_mongo.call_count, 1)
