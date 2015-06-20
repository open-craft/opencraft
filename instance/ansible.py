# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

# Imports #####################################################################

import os
import subprocess
import yaml

from tempfile import mkdtemp, mkstemp

from django.conf import settings


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Functions ###################################################################

def yaml_merge(yaml_str1, yaml_str2):
    """
    Merge the two yaml strings, overriding variables from `yaml_str1` by `yaml_str2`
    """
    if not yaml_str2:
        return yaml_str1

    result_dict = yaml.load(yaml_str1)
    for key, value in yaml.load(yaml_str2).items():
        if key in result_dict and isinstance(result_dict[key], dict) and isinstance(value, dict):
            result_dict[key].update(value)
        else:
            result_dict[key] = value
    return yaml.dump(result_dict)


def string_to_file_path(string):
    """
    Store a string in a temporary file, to pass on to a third-party shell command as a file parameter
    Returns the file path string
    """
    fd, file_path = mkstemp(text=True)
    fp = os.fdopen(fd, 'w')
    fp.write(string)
    fp.close()
    # TODO: Delete the temporary file after use
    return file_path


def run_playbook(requirements_path, inventory_str, vars_str, playbook_path, playbook_name, username='root'):
    # Ansible only supports Python 2 - so we have to run it as a separate command, in its own venv
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

    run_playbook_cmd = '{python} -u {ansible} -i {inventory_path} -e @{vars_path} -u {user} {playbook}'.format(
        python=venv_python_path,
        ansible=os.path.join(venv_path, 'bin/ansible-playbook'),
        inventory_path=string_to_file_path(inventory_str),
        vars_path=string_to_file_path(vars_str),
        user=username,
        playbook=playbook_name,
    )

    cmd = ' && '.join([create_venv_cmd, install_requirements_cmd, run_playbook_cmd])
    logger.info('Running: %s', cmd)
    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        bufsize=1, # Bufferize one line at a time
        cwd=playbook_path,
        shell=True,
    )
