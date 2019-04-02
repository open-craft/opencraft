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
OpenEdXAppServer Ansible Mixin - Tests
"""

# Imports #####################################################################

import os
from unittest.mock import patch, call, Mock

import ddt

from instance.models.mixins.ansible import Playbook
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################


@ddt.ddt
class AnsibleAppServerTestCase(TestCase):
    """
    Test cases for AnsibleAppServerMixin models
    """
    @patch_services
    def test_inventory_str(self, mocks):
        """
        Ansible inventory string - should contain the public IP of the AppServer's VM
        """
        mocks.mock_create_server.side_effect = [Mock(id='test-inventory-server'), None]
        mocks.os_server_manager.add_fixture('test-inventory-server', 'openstack/api_server_2_active.json')

        appserver = make_test_appserver()
        appserver.provision()  # This is when the server gets created
        self.assertEqual(
            appserver.inventory_str,
            '[openedx-app]\n'
            '192.168.100.200\n'
            '[app:children]\n'
            'openedx-app'
        )

    @patch_services
    def test_inventory_str_no_server(self, mocks):
        """
        Ansible inventory string - should raise an exception if the server has no public IP
        """
        appserver = make_test_appserver()
        with self.assertRaises(RuntimeError) as context:
            print(appserver.inventory_str)
        self.assertEqual(str(context.exception), "Cannot prepare to run playbooks when server has no public IP.")

    @ddt.data(
        [0, ('master', 'openedx_native.yml')],
        [0, ('open-release/ironwood.master', 'openedx_native.yml')],
        [0, ('open-release/hawthorn.1', 'edx_sandbox.yml')],
        [0, ('open-release/ginkgo.1', 'edx_sandbox.yml')],
        [1, ('master', 'openedx_native.yml')],
        [1, ('open-release/ironwood.master', 'openedx_native.yml')],
        [1, ('open-release/hawthorn.1', 'edx_sandbox.yml')],
        [1, ('open-release/ginkgo.1', 'edx_sandbox.yml')],
    )
    @ddt.unpack
    @patch('instance.ansible.poll_streams')
    @patch('instance.ansible.run_playbook')
    @patch('instance.models.openedx_appserver.OpenEdXAppServer.inventory_str')
    @patch('instance.models.mixins.ansible.open_repository')
    def test_provisioning(
            self,
            playbook_returncode,
            release_playbook_data,
            mock_open_repo,
            mock_inventory,
            mock_run_playbook,
            mock_poll_streams
    ):
        """
        The appserver gets provisioned with the appropriate playbooks.
        Failure causes later playbooks to not run.
        """
        # Unpack release and playbook data
        openedx_release, base_playbook_name = release_playbook_data
        # Create instance with pre-defined release
        instance = OpenEdXInstanceFactory(openedx_release=openedx_release)
        appserver = make_test_appserver(instance)
        working_dir = '/cloned/configuration-repo/path'
        mock_open_repo.return_value.__enter__.return_value.working_dir = working_dir
        mock_run_playbook.return_value.__enter__.return_value.returncode = playbook_returncode

        appserver.run_ansible_playbooks()

        self.assertIn(call(
            requirements_path='{}/requirements.txt'.format(working_dir),
            inventory_str=mock_inventory,
            vars_str=appserver.configuration_settings,
            playbook_path='{}/playbooks'.format(working_dir),
            playbook_name=base_playbook_name,
            username='ubuntu',
        ), mock_run_playbook.mock_calls)

        assert_func = self.assertIn if playbook_returncode == 0 else self.assertNotIn
        assert_func(call(
            requirements_path='{}/requirements.txt'.format(working_dir),
            inventory_str=mock_inventory,
            vars_str=appserver.create_common_configuration_settings(),
            playbook_path='{}/playbooks'.format(working_dir),
            playbook_name='appserver.yml',
            username='ubuntu',
        ), mock_run_playbook.mock_calls)

    @patch('instance.models.mixins.ansible.ansible.run_playbook')
    @patch('instance.models.mixins.ansible.AnsibleAppServerMixin.inventory_str')
    def test_run_playbook_logging(self, mock_inventory_str, mock_run_playbook):
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
            appserver = make_test_appserver()
            playbook = Playbook(source_repo='dummy', playbook_path='dummy', requirements_path='dummy', version='dummy',
                                variables='dummy')
            log, returncode = appserver._run_playbook("/tmp/test/working/dir/", playbook)
            self.assertCountEqual(log, ['Hello', 'Hi'])
            self.assertEqual(returncode, 0)
