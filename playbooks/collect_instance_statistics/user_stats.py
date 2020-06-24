#!/edx/bin/python.edxapp
# pylint: skip-file

from ConfigParser import ConfigParser
import os
import sys

import django


if __name__ == '__main__':
    # Set up the environment so that edX can be initialized as the LMS with the correct settings.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.openstack')
    os.environ.setdefault('SERVICE_VARIANT', 'lms')
    django.setup()

    # These modules need to be imported here because they rely on Django being already initialized
    # (e.g., the settings need to have already loaded).
    from django.contrib.auth.models import User
    from xmodule.modulestore.django import modulestore

    ms = modulestore()

    stats = {
        'users': User.objects.count(),
        'courses': len(ms.get_courses()),
    }

    # Grab the server_name_prefix passed to this script by the ansible playbook. This will be used as the
    # ConfigParser "section" name for the output data. This is so the data can easily be associated with this app
    # server by the `activity_csv` management command.
    server_name_prefix = sys.argv[1]
    public_ip = sys.argv[2]

    # Build the ConfigParser data.
    config = ConfigParser()
    config.add_section(server_name_prefix)
    for key, value in stats.items():
        config.set(server_name_prefix, key, value)

    # Output the data in ConfigParser format to stdout and to a file.
    config.write(sys.stdout)
    if len(sys.argv) > 3:
        filename = sys.argv[3]
        print >> sys.stderr, 'Writing to file passed via parameter: {filename}'.format(filename=filename)
        with open(filename, 'w') as output_file:
            config.write(output_file)
