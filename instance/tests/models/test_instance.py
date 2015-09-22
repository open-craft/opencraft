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

import re
from mock import call, patch

from instance.models.server import OpenStackServer
from instance.models.instance import InconsistentInstanceState, OpenEdXInstance
from instance.tests.base import TestCase
from instance.tests.models.factories.instance import OpenEdXInstanceFactory
from instance.tests.models.factories.server import (
    StartedOpenStackServerFactory, BootedOpenStackServerFactory, patch_os_server)


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
        server = StartedOpenStackServerFactory(instance=instance)
        self.assertEqual(instance.status, instance.STARTED)
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
        self.assertEqual(instance.github_admin_organization_name, '')
        self.assertEqual(instance.github_admin_username_list, [])
        self.assertNotIn(instance.vars_str, 'COMMON_USER_INFO')

    @patch('instance.models.instance.get_username_list_from_team')
    def test_github_admin_username_list_with_org_set(self, mock_get_username_list):
        """
        When an admin org is set, its members should be included in the ansible conf
        """
        mock_get_username_list.return_value = ['admin1', 'admin2']
        instance = OpenEdXInstanceFactory(github_admin_organization_name='test-admin-org')
        self.assertEqual(instance.github_admin_username_list, ['admin1', 'admin2'])
        self.assertIn('COMMON_USER_INFO:\n  - name: admin1\n    github: true\n    type: admin\n'
                      '  - name: admin2\n    github: true\n    type: admin', instance.vars_str)

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
        self.assertEqual(instance.inventory_str, '[app]\n192.168.100.200')

        # Server 3: 'booted'
        server3 = BootedOpenStackServerFactory(instance=instance)
        os_server_manager.add_fixture(server3.openstack_id, 'openstack/api_server_3_active.json')
        self.assertEqual(instance.inventory_str, '[app]\n192.168.100.200\n192.168.99.66')

    def test_vars_str(self):
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
        self.assertIn('EDXAPP_PLATFORM_NAME: "Vars Instance"', instance.vars_str)
        self.assertIn("EDXAPP_SITE_NAME: 'vars.test.example.com", instance.vars_str)
        self.assertIn("EDXAPP_CMS_SITE_NAME: 'studio.vars.test.example.com'", instance.vars_str)
        self.assertIn("EDXAPP_CONTACT_EMAIL: 'vars@example.com'", instance.vars_str)
        self.assertIn("edx_platform_repo: 'https://github.com/vars-org/vars-repo.git'", instance.vars_str)
        self.assertIn("edx_platform_version: '{}'".format('9' * 40), instance.vars_str)
        self.assertIn("edx_ansible_source_repo: 'http://example.org/config/repo'", instance.vars_str)
        self.assertIn("configuration_version: 'test-config-ver'", instance.vars_str)
        self.assertIn("forum_version: 'test-forum-ver'", instance.vars_str)
        self.assertIn("notifier_version: 'test-notif-ver'", instance.vars_str)
        self.assertIn("xqueue_version: 'test-xq-ver'", instance.vars_str)
        self.assertIn("certs_version: 'test-cert-ver'", instance.vars_str)

    def test_vars_str_extra_settings(self):
        """
        Add extra settings in ansible vars, which can override existing settings
        """
        instance = OpenEdXInstanceFactory(
            name='Vars Instance',
            email='vars@example.com',
            ansible_extra_settings='EDXAPP_PLATFORM_NAME: "Overriden!"',
        )
        self.assertIn('EDXAPP_PLATFORM_NAME: Overriden!', instance.vars_str)
        self.assertNotIn('Vars Instance', instance.vars_str)
        self.assertIn("EDXAPP_CONTACT_EMAIL: vars@example.com", instance.vars_str)

    @patch('instance.models.instance.OpenEdXInstance.vars_str')
    @patch('instance.models.instance.OpenEdXInstance.inventory_str')
    @patch('instance.models.instance.ansible.run_playbook')
    @patch('instance.models.instance.open_repository')
    def test_run_playbook(self, mock_open_repo, mock_run_playbook, mock_inventory, mock_vars):
        """
        Run the default playbook
        """
        instance = OpenEdXInstanceFactory()
        BootedOpenStackServerFactory(instance=instance)
        mock_open_repo.return_value.__enter__.return_value.working_dir = '/cloned/configuration-repo/path'

        instance.run_playbook()
        self.assertIn(call(
            '/cloned/configuration-repo/path/requirements.txt',
            mock_inventory,
            mock_vars,
            '/cloned/configuration-repo/path/playbooks',
            'edx_sandbox.yml',
            username='ubuntu',
        ), mock_run_playbook.mock_calls)


class OpenEdXInstanceTestCase(TestCase):
    """
    Test cases for OpenEdXInstanceMixin models
    """
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

    def test_vars_str_s3_settings(self):
        """
        Add extra settings in ansible vars, which can override existing settings
        """
        instance = OpenEdXInstanceFactory(
            s3_access_key='test-s3-access-key',
            s3_secret_access_key='test-s3-secret-access-key',
            s3_bucket_name='test-s3-bucket-name',
        )
        self.assertIn('AWS_ACCESS_KEY_ID: test-s3-access-key', instance.vars_str)
        self.assertIn('AWS_SECRET_ACCESS_KEY: test-s3-secret-access-key', instance.vars_str)
        self.assertIn('EDXAPP_AUTH_EXTRA: {AWS_STORAGE_BUCKET_NAME: test-s3-bucket-name}', instance.vars_str)
        self.assertIn('EDXAPP_AWS_ACCESS_KEY_ID: test-s3-access-key', instance.vars_str)
        self.assertIn('EDXAPP_AWS_SECRET_ACCESS_KEY: test-s3-secret-access-key', instance.vars_str)
        self.assertIn('XQUEUE_AWS_ACCESS_KEY_ID: test-s3-access-key', instance.vars_str)
        self.assertIn('XQUEUE_AWS_SECRET_ACCESS_KEY: test-s3-secret-access-key', instance.vars_str)
        self.assertIn('XQUEUE_S3_BUCKET: test-s3-bucket-name', instance.vars_str)

    @patch_os_server
    @patch('instance.models.server.openstack.create_server')
    @patch('instance.models.server.OpenStackServer.update_status')
    @patch('instance.models.server.OpenStackServer.sleep_until_status')
    @patch('instance.models.server.OpenStackServer.reboot')
    @patch('instance.models.instance.gandi.set_dns_record')
    @patch('instance.models.instance.OpenEdXInstance.run_playbook')
    def test_provision(self, os_server_manager, mock_run_playbook, mock_set_dns_record, mock_server_reboot,
                       mock_sleep_until_status, mock_update_status, mock_openstack_create_server):
        """
        Run provisioning sequence
        """
        mock_openstack_create_server.return_value.id = 'test-run-provisioning-server'
        os_server_manager.add_fixture('test-run-provisioning-server', 'openstack/api_server_2_active.json')

        instance = OpenEdXInstanceFactory(sub_domain='run.provisioning')
        instance.provision()
        self.assertEqual(mock_set_dns_record.mock_calls, [
            call(name='run.provisioning', type='A', value='192.168.100.200'),
            call(name='studio.run.provisioning', type='CNAME', value='run.provisioning'),
        ])
        self.assertEqual(mock_run_playbook.call_count, 1)
        self.assertEqual(mock_server_reboot.call_count, 1)

    @patch_os_server
    @patch('instance.models.server.OpenStackServer.update_status', autospec=True)
    @patch('instance.models.server.time.sleep')
    @patch('instance.models.server.OpenStackServer.reboot')
    @patch('instance.models.instance.gandi.set_dns_record')
    @patch('instance.models.instance.OpenEdXInstance.run_playbook')
    def test_provision_no_active(self, os_server_manager, mock_run_playbook, mock_set_dns_record,
                                 mock_server_reboot, mock_sleep, mock_update_status):
        """
        Run provisioning sequence, with status jumping from 'started' to 'booted' (no 'active')
        """
        instance = OpenEdXInstanceFactory(sub_domain='run.provisioning.noactive')
        status_queue = [
            OpenStackServer.STARTED,
            OpenStackServer.BOOTED,
            OpenStackServer.BOOTED,
            OpenStackServer.PROVISIONED,
            OpenStackServer.REBOOTING,
            OpenStackServer.READY,
        ]
        status_queue.reverse() # To be able to use pop()

        def update_status(self, provisioned=False, rebooting=False):
            """ Simulate status progression successive runs """
            self.status = status_queue.pop()
        mock_update_status.side_effect = update_status

        with patch('instance.models.server.OpenStackServer.start'):
            instance.provision()
        self.assertEqual(mock_run_playbook.call_count, 1)
