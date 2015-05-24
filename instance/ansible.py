# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

# Imports #####################################################################

import os
import subprocess
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


def run_playbook(inventory_str, vars_str, inventory, username='root'):
    # Ansible only supports Python 2 - so we have to run it as a separate command, in its own venv
    return subprocess.Popen(
        [
            os.path.join(settings.ANSIBLE_ENV_BIN_PATH, 'python'),
            '-u',
            os.path.join(settings.ANSIBLE_ENV_BIN_PATH, 'ansible-playbook'),
            '-i', string_to_file_path(inventory_str),
            '-e', '@' + string_to_file_path(vars_str),
            '-u', username,
            inventory,
        ],
        stdout=subprocess.PIPE,
        bufsize=1, # Bufferize one line at a time
        cwd=os.path.join(settings.CONFIGURATION_REPO_PATH, 'playbooks'),
    )
