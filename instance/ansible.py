# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

# Imports #####################################################################

import os
import subprocess
import yaml

from tempfile import mkstemp

from django.conf import settings


# Functions ###################################################################

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


def run_playbook(inventory_str, vars_str, playbook_path, playbook_name, username='root'):
    # Ansible only supports Python 2 - so we have to run it as a separate command, in its own venv
    return subprocess.Popen(
        [
            os.path.join(settings.ANSIBLE_ENV_BIN_PATH, 'python'),
            '-u',
            os.path.join(settings.ANSIBLE_ENV_BIN_PATH, 'ansible-playbook'),
            '-i', string_to_file_path(inventory_str),
            '-e', '@' + string_to_file_path(vars_str),
            '-u', username,
            playbook_name,
        ],
        stdout=subprocess.PIPE,
        bufsize=1, # Bufferize one line at a time
        cwd=playbook_path,
    )
