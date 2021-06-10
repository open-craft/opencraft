#!/edx/app/edxapp/venvs/edxapp/bin/python
# pylint: skip-file

from __future__ import print_function
from argparse import ArgumentParser
from datetime import datetime, timedelta
import gzip
import os
import re
import sys

import django
from django.utils import timezone

from six.moves.configparser import ConfigParser


# This regex pattern is used to extract the IPv4 address from the beginning of each line in the Nginx access logs.
NGINX_ACCESS_PATTERN = re.compile(r'- - (?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
LOG_PATH = '/edx/var/log/nginx'

def valid_date(s):
    """
    Verify that the string passed in is a date
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


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
    parser.add_argument(
        '--start-date',
        default=None,
        type=valid_date,
        help='The first day on which statistics should be gathered. FORMAT: YYYY-MM-DD'
    )
    parser.add_argument(
        '--end-date',
        default=None,
        type=valid_date,
        help='The last day on which statistics should be gathered.'
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

    start_date = args.start_date
    end_date = args.end_date

    if start_date is None or end_date is None:
        # If a time interval is not passed as arguments
        # get the active users for the last full month.
        beginning_of_this_month = datetime.now(tz=timezone.utc).replace(day=1)
        end_of_last_month = beginning_of_this_month - timedelta(days=1)
        beginning_of_last_month = end_of_last_month.replace(day=1)

        start_date = beginning_of_last_month
        end_date = end_of_last_month

    stats = {
        'users': User.objects.count(),
        'active_users': User.objects.filter(last_login__range=(start_date, end_date)).count(),
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
