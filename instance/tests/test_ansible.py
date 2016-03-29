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
Ansible - Tests
"""

# Imports #####################################################################

import os.path
from unittest import mock
from unittest.mock import patch

import yaml

from instance import ansible
from instance.tests.base import TestCase


# Tests #######################################################################

class YAMLTestCase(TestCase):
    """
    Test cases for YAML helper functions
    """
    def setUp(self):
        super().setUp()

        self.yaml_dict1 = {
            'testa': 'firsta with unicode «ταБЬℓσ»',
            'testb': 'firstb',
            'test_dict': {
                'foo': 'firstfoo',
                'bar': 'firstbar',
                'recursive': {
                    'a': 1,
                },
            },
        }
        self.yaml_dict2 = {
            'testb': 'secondb with unicode «ταБЬℓσ2»',
            'testc': 'secondc',
            'test_dict': {
                'foo': 'secondfoo',
                'other': 'secondother',
                'recursive': {
                    'b': 2,
                },
            }
        }
        self.yaml_str1 = yaml.dump(self.yaml_dict1)
        self.yaml_str2 = yaml.dump(self.yaml_dict2)

    def test_yaml_merge(self):
        """
        Merge of two yaml strings with overlapping variables
        """
        yaml_result_str = ansible.yaml_merge(self.yaml_str1, self.yaml_str2)
        self.assertEqual(yaml.load(yaml_result_str), {
            'testa': 'firsta with unicode «ταБЬℓσ»',
            'testb': 'secondb with unicode «ταБЬℓσ2»',
            'testc': 'secondc',
            'test_dict': {
                'foo': 'secondfoo',
                'bar': 'firstbar',
                'other': 'secondother',
                'recursive': {
                    'a': 1,
                    'b': 2,
                },
            }
        })

    def test_yaml_merge_with_none(self):
        """
        Merge of a yaml string with None
        """
        self.assertEqual(ansible.yaml_merge(self.yaml_str1, None), self.yaml_str1)


class AnsibleTestCase(TestCase):
    """
    Test cases for ansible helper functions & wrappers
    """
    def test_run_playbook(self):
        """
        Run the ansible-playbook command
        """

        popen_result = object()

        with patch('instance.ansible.render_sandbox_creation_command', return_value="ANSIBLE CMD") as mock_render, \
                patch('instance.ansible.create_temp_dir') as mock_create_temp, \
                patch('instance.ansible.string_to_file_path', return_value='/tmp/string/file'), \
                patch('subprocess.Popen', return_value=popen_result) as mock_popen:

            mock_create_temp.return_value.__enter__.return_value = '/tmp/tempdir'

            with ansible.run_playbook(
                requirements_path="/tmp/requirements.txt",
                inventory_str="INVENTORY: 'str'",
                vars_str="VARS: 'str2'",
                playbook_path='/play/book',
                playbook_name='playbook_name'
            ) as run_playbook_result:

                # This checks if run_playbook returns a Process object (or more precisely: object returned from Popen)
                self.assertEqual(run_playbook_result, popen_result)

            mock_render.assert_called_once_with(
                inventory_path='/tmp/string/file',
                vars_path='/tmp/string/file',
                requirements_path='/tmp/requirements.txt',
                playbook_name='playbook_name',
                remote_username='root',
                venv_path='/tmp/tempdir/venv'
            )

            mock_popen.assert_called_once_with(
                "ANSIBLE CMD", bufsize=1, stdout=-1, stderr=-1, cwd='/play/book', shell=True, env=mock.ANY
            )
            call_kwargs = mock_popen.mock_calls[0][2]
            self.assertIn('env', call_kwargs)
            self.assertEqual(call_kwargs['env']['TMPDIR'], '/tmp/tempdir')

    def test_render_command(self):
        """
        Run the render_sandbox_creation_command function
        """

        run_playbook_command = ansible.render_sandbox_creation_command(
            requirements_path='/requirements/path.txt',
            inventory_path="/tmp/inventory/path",
            vars_path="/tmp/vars/path",
            playbook_name='playbook_name',
            remote_username="root",
            venv_path='/tmp/venv'
        )
        expected = (
            'virtualenv -p /usr/bin/python /tmp/venv && '
            '/tmp/venv/bin/python -u /tmp/venv/bin/pip install -r /requirements/path.txt && '
            '/tmp/venv/bin/python -u /tmp/venv/bin/ansible-playbook -i /tmp/inventory/path '
            '-e @/tmp/vars/path -u root playbook_name'
        )

        self.assertEqual(expected, run_playbook_command)

    def test_create_temp_dir_ok(self):
        """
        Check if create_temp_dir behaves correctly when no exception is
        raised from inside it.

        By behave correctly we mean: creates and returns a tempdir, which
        is deleted after we exit the context manager.
        """
        with ansible.create_temp_dir() as temp_dir:
            self.assertTrue(os.path.exists(temp_dir))
            self.assertTrue(os.path.isdir(temp_dir))
        self.assertFalse(os.path.exists(temp_dir))

    def test_create_temp_dir_exception(self):
        """
        Check if create_temp_dir behaves correctly when an exception is
        raised from inside it.

        By behave correctly we mean: creates and returns a tempdir, which
        is deleted after we exit the context manager.
        """
        saved_temp_dir = None
        with self.assertRaises(KeyboardInterrupt):
            with ansible.create_temp_dir() as temp_dir:
                saved_temp_dir = temp_dir
                self.assertTrue(os.path.exists(temp_dir))
                self.assertTrue(os.path.isdir(temp_dir))
                raise KeyboardInterrupt()
        self.assertIsNotNone(saved_temp_dir)
        self.assertFalse(os.path.exists(saved_temp_dir))

    def test_string_to_file_path_ok(self):
        """
        Check if string_to_file_path creates a file with proper contents.
        """
        file_path = ansible.string_to_file_path("TEST ąęłźżó")
        try:
            with open(file_path, 'r') as f:
                self.assertEqual("TEST ąęłźżó", f.read())
        finally:
            os.remove(file_path)
