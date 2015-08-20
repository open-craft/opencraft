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
Ansible - Helper functions
"""

# Imports #####################################################################

import os
import subprocess
import yaml

from contextlib import contextmanager
from tempfile import mkdtemp, mkstemp

from django.conf import settings


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Functions ###################################################################

def yaml_merge(yaml_str1, yaml_str2):
    """
    Merge the two yaml strings, recursively overriding variables from `yaml_str1` by `yaml_str2`
    """
    if not yaml_str2:
        return yaml_str1

    dict1 = yaml.load(yaml_str1)
    dict2 = yaml.load(yaml_str2)
    result_dict = dict_merge(dict1, dict2)

    return yaml.dump(result_dict)


def dict_merge(dict1, dict2):
    """
    Merge the two dicts, recursively overriding keys from `dict1` by `dict2`
    """
    result_dict = dict1.copy()
    for key in dict2:
        if key in result_dict and isinstance(result_dict[key], dict) and isinstance(dict2[key], dict):
            result_dict[key] = dict_merge(result_dict[key], dict2[key])
        else:
            result_dict[key] = dict2[key]
    return result_dict


@contextmanager
def string_to_file_path(string):
    """
    Store a string in a temporary file, to pass on to a third-party shell command as a file parameter
    Returns the file path string
    """
    fd, file_path = mkstemp(text=True)
    fp = os.fdopen(fd, 'w')
    fp.write(string)
    fp.close()
    yield file_path
    os.remove(file_path)


@contextmanager
def run_playbook(requirements_path, inventory_str, vars_str, playbook_path, playbook_name, username='root'):
    """
    Runs ansible-playbook in a dedicated venv

    Ansible only supports Python 2 - so we have to run it as a separate command, in its own venv
    """
    venv_path = mkdtemp()
    create_venv_cmd = 'virtualenv -p {python_path} {venv_path}'.format(
        python_path=settings.ANSIBLE_PYTHON_PATH,
        venv_path=venv_path,
    )

    venv_python_path = os.path.join(venv_path, 'bin/python')
    install_requirements_cmd = '{python} -u {pip} install -r {requirements_path}'.format(
        python=venv_python_path,
        pip=os.path.join(venv_path, 'bin/pip'),
        requirements_path=requirements_path,
    )

    with string_to_file_path(inventory_str) as inventory_path:
        with string_to_file_path(vars_str) as vars_path:
            run_playbook_cmd = '{python} -u {ansible} -i {inventory_path} -e @{vars_path} -u {user} {playbook}'\
                .format(
                    python=venv_python_path,
                    ansible=os.path.join(venv_path, 'bin/ansible-playbook'),
                    inventory_path=inventory_path,
                    vars_path=vars_path,
                    user=username,
                    playbook=playbook_name,
                )

            cmd = ' && '.join([create_venv_cmd, install_requirements_cmd, run_playbook_cmd])
            logger.info('Running: %s', cmd)
            yield subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                bufsize=1, # Bufferize one line at a time
                cwd=playbook_path,
                shell=True,
            )
