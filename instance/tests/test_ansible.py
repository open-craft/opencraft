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
import yaml

from unittest.mock import call, patch

from instance import ansible
from instance.tests.base import TestCase


# Tests #######################################################################

class YAMLTestCase(TestCase):
    """
    Test cases for YAML helper functions
    """
    def setUp(self):
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
        self.assertEquals(yaml.load(yaml_result_str), {
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
    def test_string_to_file_path(self):
        """
        Store a string in a temporary file
        """
        test_str = 'My kewl string\nwith unicode «ταБЬℓσ», now 20% off!'
        file_path_copy = None
        with ansible.string_to_file_path(test_str) as file_path:
            with open(file_path) as fp:
                self.assertEqual(fp.read(), test_str)
            file_path_copy = file_path
            self.assertTrue(os.path.isfile(file_path_copy))
        self.assertFalse(os.path.isfile(file_path_copy))

    @patch('subprocess.Popen')
    @patch('instance.ansible.mkdtemp')
    @patch('instance.ansible.string_to_file_path')
    def test_run_playbook(self, mock_string_to_file_path, mock_mkdtemp, mock_popen):
        """
        Run the ansible-playbook command
        """
        mock_string_to_file_path.return_value.__enter__.return_value = '/test/str2path'
        mock_mkdtemp.return_value = '/test/mkdtemp'

        with ansible.run_playbook('/requirements/path.txt',
                                  "INVENTORY: 'str'",
                                  "VARS: 'str2'",
                                  '/play/book',
                                  'playbook_name_str'):
            run_playbook_cmd = (
                'virtualenv -p /usr/bin/python /test/mkdtemp && '
                '/test/mkdtemp/bin/python -u /test/mkdtemp/bin/pip install -r /requirements/path.txt && '
                '/test/mkdtemp/bin/python -u /test/mkdtemp/bin/ansible-playbook -i /test/str2path '
                '-e @/test/str2path -u root playbook_name_str'
            )
            self.assertEqual(
                mock_popen.mock_calls,
                [call(run_playbook_cmd, bufsize=1, stdout=-1, cwd='/play/book', shell=True)]
            )
