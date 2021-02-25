#!/edx/bin/python.edxapp
# pylint: skip-file

from __future__ import print_function
from argparse import ArgumentParser
import gzip
import os
import re
import sys

import django

from six.moves.configparser import ConfigParser


# This regex pattern is used to extract the IPv4 address from the beginning of each line in the Nginx access logs.
NGINX_ACCESS_PATTERN = re.compile(r'- - (?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
LOG_PATH = '/edx/var/log/nginx'


if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument(
        '--config-section',
        default=None,
        help='The header for the section in the output yml that the statistics will be assigned',
        required=True
    )
    parser.add_argument(
        '--out',
        default=None,
        help='Path to the output file of the new CSV. Leave blank to use stdout.'
    )
    parser.add_argument(
        '--skip-hit-statistics',
        default=False,
        action='store_true',
        help='Whether to skip the hit statistics'
    )
    args = parser.parse_args()

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

    if not args.skip_hit_statistics:
        # Produce the paths to all of the "access.log*" files in the Nginx log directory to be parsed.
        log_files = [
            f for f in os.listdir(LOG_PATH)
            if os.path.isfile(os.path.join(LOG_PATH, f)) and f.startswith('access.log')
        ]

        # Walk through all of the Nginx logs, storing the found remote host IP addresses in a set to enforce uniqueness.
        unique_hits = set()
        total_hits = 0
        for file in log_files:
            print('Parsing log file: {file}'.format(file=file), file=sys.stderr)

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
                    total_hits += 1
                    unique_hits.add(match.group('ipaddress'))
            handle.close()

        stats['unique_hits'] = len(unique_hits)
        stats['total_hits'] = total_hits

    # Build the ConfigParser data.
    config = ConfigParser()
    config.add_section(args.config_section)
    for key, value in stats.items():
        config.set(args.config_section, key, str(value))

    # Output the data in ConfigParser format to stdout and to a file.
    config.write(sys.stdout)
    if args.out:
        print('Writing to file passed via parameter: {filename}'.format(filename=args.out), file=sys.stderr)
        with open(args.out, 'w') as output_file:
            config.write(output_file)
