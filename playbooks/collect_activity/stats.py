#!/edx/bin/python.edxapp
# pylint: skip-file

from configparser import ConfigParser
import gzip
import os
import re
import sys

import django


# This regex pattern is used to extract the IPv4 address from the beginning of each line in the Nginx access logs.
NGINX_ACCESS_PATTERN = re.compile(r'- - (?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
LOG_PATH = '/edx/var/log/nginx'


if __name__ == '__main__':
    # Set up the environment so that edX can be initialized as the LMS with the correct settings.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.envs.openstack')
    os.environ.setdefault('SERVICE_VARIANT', 'lms')
    django.setup()

    # These modules need to be imported here because they rely on Django being already initialized
    # (e.g., the settings need to have already loaded).
    from django.contrib.auth.models import User
    from xmodule.modulestore.django import modulestore

    # Produce the paths to all of the "access.log*" files in the Nginx log directory to be parsed.
    log_files = [
        f for f in os.listdir(LOG_PATH)
        if os.path.isfile(os.path.join(LOG_PATH, f)) and f.startswith('access.log')
    ]

    # Walk through all of the Nginx logs, storing the found remote host IP addresses in a set to enforce uniqueness.
    unique_hits = set()
    for file in log_files:
        print >> sys.stderr, 'Parsing log file: {file}'.format(file=file)

        file_path = os.path.join(LOG_PATH, file)
        # Make sure we use gzip to decompress any compressed log files.
        if file.endswith('.gz'):
            handle = gzip.open(file_path, 'rb')
        else:
            handle = open(file_path, 'r')

        # Run each access log line through a regex to extract the IPv4 addresses of remote hosts.
        for line in handle:
            match = re.match(NGINX_ACCESS_PATTERN, line)
            if match:
                unique_hits.add(match.group('ipaddress'))
        handle.close()

    ms = modulestore()

    stats = {
        'users': User.objects.count(),
        'courses': len(ms.get_courses()),
        'hits': len(unique_hits),
    }

    # Grab the hostname address address passed to this script by the ansible playbook. This will be used as the
    # ConfigParser "section" name for the output data. This is so the data can easily be associated with this app
    # server by the `activity_csv` management command.
    public_ip = sys.argv[1]

    # Build the ConfigParser data.
    config = ConfigParser()
    config.add_section(public_ip)
    for key, value in stats.items():
        config.set(public_ip, key, value)

    # Output the data in ConfigParser format to stdout and to a file.
    config.write(sys.stdout)
    if len(sys.argv) > 2:
        filename = sys.argv[2]
        print >> sys.stderr, 'Writing to file passed via parameter: {filename}'.format(filename=filename)
        with open(filename, 'w') as output_file:
            config.write(output_file)
