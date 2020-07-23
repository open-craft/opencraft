# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <contact@opencraft.com>
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
Instance app - Activity report management command
"""

# Imports #####################################################################

import argparse
from configparser import ConfigParser
import csv
from datetime import datetime, timedelta
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from instance import ansible
from instance.models.openedx_instance import OpenEdXInstance
from registration.models import BetaTestApplication


def valid_date(s):
    """
    Verify that the string passed in is a date no later than today (UTC)
    """
    try:
        date = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError("Not a valid date: '{0}'.".format(s))

    if date <= datetime.utcnow().date():
        return s

    raise argparse.ArgumentTypeError("Date must be earlier than or equal to today: '{0}'.".format(s))


# Classes #####################################################################


class Command(BaseCommand):
    """
    Instance_statistics_csv management command class
    """
    help = (
        'Generates a CSV containing basic activity information for the given instance'
        ' (numbers for hits, distinct hits, users, and courses).'
    )

    DEFAULT_NUM_DAYS = 30

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            '-d',
            default=None,
            help='The fully qualified domain of the instance to get the data for',
            required=True
        )
        parser.add_argument(
            '--start-date',
            default=(
                datetime.utcnow().date() - timedelta(days=self.DEFAULT_NUM_DAYS)
            ).strftime("%Y-%m-%d"),
            type=valid_date,
            help='The first day on which statistics should be gathered. '
            'Defaults to {num_days_ago} days ago (UTC).'
            'FORMAT: YYYY-MM-DD'.format(num_days_ago=self.DEFAULT_NUM_DAYS)
        )
        parser.add_argument(
            '--end-date',
            default=datetime.utcnow().date().strftime("%Y-%m-%d"),
            type=valid_date,
            help='The last day on which statistics should be gathered. '
            'Defaults to today (UTC).'
            'FORMAT: YYYY-MM-DD'
        )
        parser.add_argument(
            '--out',
            default=None,
            help='Path to the output file of the new CSV. Leave blank to use stdout.'
        )

    def handle(self, *args, **options):
        # Determine the stream to be used for outputting the CSV.
        if options['out'] is None:
            out = self.stdout
        else:
            try:
                out = open(options['out'], 'w')
            except PermissionError:
                self.stderr.write(self.style.ERROR(
                    'Permission denied while attempting to write '
                    'file: {outfile}'.format(
                        outfile=options['out']
                    )
                ))
                sys.exit(1)

        start_date = datetime.strptime(options['start_date'], "%Y-%m-%d").date()
        end_date = datetime.strptime(options['end_date'], "%Y-%m-%d").date()

        # Verify that --end-date is greater than or equal to --start-date
        if end_date < start_date:
            self.stderr.write(self.style.ERROR(
                '--end-date ({end_date}) must be later than or equal '
                'to --start-date ({start_date})'.format(
                    end_date=end_date,
                    start_date=start_date
                )
            ))
            sys.exit(1)

        self.collect_instance_statistics(out, options['domain'], start_date, end_date)

    def get_instance_from_domain_name(self, domain_name):
        """ Get an instance object for a given domain name """
        try:
            instance = OpenEdXInstance.objects.get(
                Q(external_lms_domain=domain_name) | Q(internal_lms_domain=domain_name)
            )
        except OpenEdXInstance.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'No OpenEdXInstance exists with an external or internal '
                'domain of {domain_name}'.format(
                    domain_name=domain_name
                )
            ))
            sys.exit(1)

        # If there are no active appservers for the instance, we should error out
        if not instance.successfully_provisioned or not instance.get_active_appservers():
            self.stderr.write(self.style.ERROR(
                'No active OpenEdXAppServers exist for the instance with '
                'external or internal domain of {domain_name}'.format(
                    domain_name=domain_name
                )
            ))
            sys.exit(1)

        return instance

    def get_elasticsearch_hits_data_summary(self, playbook_output_dir, name_prefix, start_date, end_date):
        """ Execute the collect_elasticsearch_data playbook to gather statistics """
        if not settings.INSTANCE_LOGS_SERVER_HOST:
            self.stderr.write(self.style.WARNING(
                'Skipping Elasticsearch data collection because '
                'INSTANCE_LOGS_SERVER_HOST is unset'
            ))
            return

        inventory = '[apps]\n{server}'.format(server=settings.INSTANCE_LOGS_SERVER_HOST)
        playbook_path = os.path.join(
            settings.SITE_ROOT,
            'playbooks/collect_instance_statistics/collect_elasticsearch_data.yml'
        )

        def log_line(line):
            """Helper to pass to capture_playbook_output()."""
            self.stderr.write(self.style.SUCCESS(line))
        log_line.info = log_line
        log_line.error = log_line

        # Launch the collect_elasticsearch_data playbook, which places a file into the `playbook_output_dir`
        # on this host.
        ansible.capture_playbook_output(
            requirements_path=os.path.join(
                os.path.dirname(playbook_path),
                'requirements.txt'
            ),
            inventory_str=inventory,
            vars_str=(
                'local_output_dir: {output_dir}\n'
                'remote_output_filename: /tmp/activity_report\n'
                'server_name_prefix: {server_name_prefix}\n'
                'start_date: {start_date}\n'
                'end_date: {end_date}'
            ).format(
                output_dir=playbook_output_dir,
                server_name_prefix=name_prefix,
                start_date=start_date,
                end_date=end_date
            ),
            playbook_path=playbook_path,
            username=settings.INSTANCE_LOGS_SERVER_SSH_USERNAME,
            logger_=log_line,
        )

    def get_instance_usage_data(self, playbook_output_dir, name_prefix, public_ip):
        """ Execute the collect_activity playbook to gather statistics """
        inventory = '[apps]\n{server}'.format(server=public_ip)
        playbook_path = os.path.join(
            settings.SITE_ROOT,
            'playbooks/collect_activity/collect_activity.yml'
        )

        def log_line(line):
            """Helper to pass to capture_playbook_output()."""
            self.stderr.write(self.style.SUCCESS(line))
        log_line.info = log_line
        log_line.error = log_line

        playbook_extra_script_arguments = '--skip-hit-statistics' if settings.INSTANCE_LOGS_SERVER_HOST else ''

        # Launch the collect_activity playbook, which places a file into the `playbook_output_dir`
        # on this host.
        ansible.capture_playbook_output(
            requirements_path=os.path.join(os.path.dirname(playbook_path), 'requirements.txt'),
            inventory_str=inventory,
            vars_str=(
                'local_output_dir: {output_dir}\n'
                'local_output_filename: user_statistics\n'
                'remote_output_filename: /tmp/activity_report\n'
                'config_section: {config_section}\n'
                'extra_script_arguments: {extra_script_arguments}'
            ).format(
                output_dir=playbook_output_dir,
                config_section=name_prefix,
                extra_script_arguments=playbook_extra_script_arguments
            ),
            playbook_path=playbook_path,
            username=settings.INSTANCE_LOGS_SERVER_SSH_USERNAME,
            logger_=log_line,
        )

    def collect_instance_statistics(
            self,
            out,
            domain_name,
            start_date,
            end_date
    ):  # pylint: disable=too-many-locals
        """Generate the instance statistics CSV."""
        instance = self.get_instance_from_domain_name(domain_name)
        appserver = instance.get_active_appservers().first()
        name_prefix = appserver.server_name_prefix

        self.stderr.write(self.style.SUCCESS('Running playbook...'))

        with ansible.create_temp_dir() as playbook_output_dir:
            self.get_elasticsearch_hits_data_summary(playbook_output_dir, name_prefix, start_date, end_date)
            self.get_instance_usage_data(playbook_output_dir, name_prefix, appserver.server.public_ip)

            csv_writer = csv.writer(out, quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writerow([
                'Fully Qualified Domain Name',
                'Server Name Prefix',
                'Name',
                'Contact Email',
                'Unique Hits',
                'Total Hits',
                'Total Courses',
                'Total Users',
                'Age (Days)'
            ])

            filenames = [os.path.join(playbook_output_dir, f) for f in os.listdir(playbook_output_dir)]
            data = ConfigParser()
            data.read(filenames)

            try:
                section = data[name_prefix]
            except KeyError:
                # Set the section to an empty dict
                section = {}

            instance_age = datetime.now(instance.created.tzinfo) - instance.created

            try:
                email = instance.betatestapplication_set.get().user.email
            except BetaTestApplication.DoesNotExist:
                email = 'N/A'

            csv_writer.writerow([
                instance.domain,
                name_prefix,
                instance.ref.name,
                email,
                section.get('unique_hits', 'N/A'),
                section.get('total_hits', 'N/A'),
                section.get('courses', 'N/A'),
                section.get('users', 'N/A'),
                instance_age.days
            ])

            self.stderr.write(self.style.SUCCESS('Done generating CSV output.'))
