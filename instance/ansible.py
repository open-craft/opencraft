# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

# Load django environment #####################################################

import os
import sys
import django
sys.path.append('/home/antoviaque/prog/opencraft')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opencraft.dev")
django.setup()


# Imports #####################################################################

from pprint import pprint #pylint: disable=unused-import
import subprocess
from tempfile import mkstemp

from django.conf import settings


# Constants ###################################################################

INVENTORY_STR = '''
[app]
{server_ip}
'''

VARS_STR = '''
# edxapp
EDXAPP_PLATFORM_NAME: '{name}'
EDXAPP_LMS_NGINX_PORT: 80
EDXAPP_LMS_NGINX_SSL_PORT: 443
EDXAPP_SITE_NAME: '{domain}'
EDXAPP_LMS_SITE_NAME: $EDXAPP_SITE_NAME
EDXAPP_LMS_BASE: $EDXAPP_SITE_NAME
EDXAPP_PREVIEW_LMS_BASE: $EDXAPP_SITE_NAME

EDXAPP_CMS_SITE_NAME: '{domain}:18010'
EDXAPP_CMS_BASE: $EDXAPP_SITE_NAME

# Forum environment settings
FORUM_RACK_ENV: 'production'
FORUM_SINATRA_ENV: 'production'

# Emails
EDXAPP_CONTACT_EMAIL: '{email}'
EDXAPP_TECH_SUPPORT_EMAIL: $EDXAPP_CONTACT_EMAIL
EDXAPP_BUGS_EMAIL: $EDXAPP_CONTACT_EMAIL
EDXAPP_FEEDBACK_SUBMISSION_EMAIL: $EDXAPP_CONTACT_EMAIL
EDXAPP_DEFAULT_FROM_EMAIL: $EDXAPP_CONTACT_EMAIL
EDXAPP_DEFAULT_FEEDBACK_EMAIL: $EDXAPP_CONTACT_EMAIL
EDXAPP_SERVER_EMAIL: $EDXAPP_CONTACT_EMAIL
EDXAPP_BULK_EMAIL_DEFAULT_FROM_EMAIL: $EDXAPP_CONTACT_EMAIL

# Misc
EDXAPP_TIME_ZONE: 'UTC'

# Pin down dependencies to specific (known to be compatible) commits.
edx_platform_repo: 'https://github.com/edx/edx-platform.git'
edx_platform_version: 'master'
edx_ansible_source_repo: 'https://github.com/edx/configuration.git'
configuration_version: 'master'

# Features
EDXAPP_FEATURES:
  USE_MICROSITES: false
  AUTH_USE_OPENID: false
  ENABLE_DISCUSSION_SERVICE: true
  ENABLE_INSTRUCTOR_ANALYTICS: true
  ENABLE_INSTRUCTOR_EMAIL: true
  REQUIRE_COURSE_EMAIL_AUTH: false
  ENABLE_PEARSON_HACK_TEST: false
  SUBDOMAIN_BRANDING: false
  SUBDOMAIN_COURSE_LISTINGS: false
  PREVIEW_LMS_BASE: $EDXAPP_PREVIEW_LMS_BASE
  ENABLE_DJANGO_ADMIN_SITE: true
  ALLOW_ALL_ADVANCED_COMPONENTS: true
'''


# Functions ###################################################################

def get_inventory_str(server_ip):
    return INVENTORY_STR.format(server_ip=server_ip)

def get_vars_str(name, domain, email='contact@example.com'):
    return VARS_STR.format(
        name=name,
        domain=domain,
        email=email,
    )

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


def run_ansible_playbook(inventory_str, vars_str, inventory, username='ubuntu'):
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


# Main ########################################################################

def main():
    run_ansible_playbook(
        get_inventory_str('92.222.83.123'),
        get_vars_str('OpenCraft Sandbox 4', 'sandbox4.openedxhosting.com'),
        'edx_sandbox.yml',
        username='admin',
    )

if __name__ == '__main__':
    main()
