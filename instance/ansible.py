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
import shutil
import subprocess
import sys
import traceback
import yaml

from contextlib import contextmanager
from tempfile import mkdtemp, NamedTemporaryFile

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
    dict1 = dict1.copy()
    for key in dict2:
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
            dict1[key] = dict_merge(dict1[key], dict2[key])
        else:
            dict1[key] = dict2[key]
    return dict1


def string_to_file_path(string, root_dir=None):
    """
    Store a string in a temporary file
    """
    f = NamedTemporaryFile('w', delete=False, dir=root_dir)
    f.write(string)
    f.close()
    return f.name


def on_remove_error(*args):
    """
    A helper function intended to be passed to shutil.rmtree as oneror argiment.

    The only reason it is public is to unittest it.
    """
    exctype, value = sys.exc_info()[:2]
    exception_message = '\n'.join(traceback.format_exception_only(exctype, value)).strip()
    logger.warning(
        "Error while deleting temporary directory, this is not related to VM "
        "creation, but might fill /tmp directory of the IM.\n Exception "
        "is %s", exception_message
    )


@contextmanager
def create_temp_dir():
    """
    A context manager that creates a temporary directory, returns it. Directory is deleted upon context manager exit.
    """
    temp_dir = None
    try:
        temp_dir = mkdtemp()
        yield temp_dir
    finally:
        # If tempdir is None it means that if wasn't created, so we don't need to delete it
        if temp_dir is not None:
            # This is really a "best effort" solution, if something will
            # block the deletion (like file being locked somehow)
            # this should just move on rather than raise.
            shutil.rmtree(temp_dir, onerror=on_remove_error)


def render_sandbox_creation_command(
        requirements_path, inventory_path, vars_path, playbook_name, remote_username, venv_path):
    """
    Renders the shell command used to create the sandbox
    """

    venv_python_path = os.path.join(venv_path, 'bin/python')
    create_venv_cmd = 'virtualenv -p {python_path} {venv_path}'.format(
        python_path=settings.ANSIBLE_PYTHON_PATH,
        venv_path=venv_path,
    )

    install_requirements_cmd = '{python} -u {pip} install -r {requirements_path}'.format(
        python=venv_python_path,
        pip=os.path.join(venv_path, 'bin/pip'),
        requirements_path=requirements_path,
    )

    run_playbook_cmd = '{python} -u {ansible} -i {inventory_path} -e @{vars_path} -u {user} {playbook}'.format(
        python=venv_python_path,
        ansible=os.path.join(venv_path, 'bin/ansible-playbook'),
        inventory_path=inventory_path,
        vars_path=vars_path,
        user=remote_username,
        playbook=playbook_name,
    )

    return ' && '.join([create_venv_cmd, install_requirements_cmd, run_playbook_cmd])


@contextmanager
def run_playbook(requirements_path, inventory_str, vars_str, playbook_path, playbook_name, username='root'):
    """
    Runs ansible-playbook in a dedicated venv

    Ansible only supports Python 2 - so we have to run it as a separate command, in its own venv
    """

    with create_temp_dir() as ansible_tmp_dir:

        vars_path = string_to_file_path(vars_str, root_dir=ansible_tmp_dir)
        inventory_path = string_to_file_path(inventory_str, root_dir=ansible_tmp_dir)
        venv_path = os.path.join(ansible_tmp_dir, 'venv')

        cmd = render_sandbox_creation_command(
            requirements_path=requirements_path,
            inventory_path=inventory_path,
            vars_path=vars_path,
            playbook_name=playbook_name,
            remote_username=username,
            venv_path=venv_path
        )

        logger.info('Running: %s', cmd)

        # Override TMPDIR environmental variable so any temp files created by ansible (and anything else)
        # are created in a directory that we will safely delete after this command exits
        env = dict(os.environ)
        env['TMPDIR'] = ansible_tmp_dir

        yield subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1, # Buffer one line at a time
            cwd=playbook_path,
            shell=True,
            env=env,
        )
