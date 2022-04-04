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
            '--domains',
            '-d',
            default=None,
            help='Comma-separated list of fully qualified domains of the instances to get the data for',
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

        domains = options['domains'].split(',')

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

        self.collect_instance_statistics(out, domains, start_date, end_date)

    def get_instances_from_domain_names(self, domain_names):
        """ Get an instance object for a given domain name """
        instances = OpenEdXInstance.objects \
            .filter(ref_set__openedxappserver_set___is_active=True) \
            .filter(successfully_provisioned=True) \
            .filter(
                Q(external_lms_domain__in=domain_names) | Q(internal_lms_domain__in=domain_names)
            )

        if not instances:
            self.stderr.write(self.style.ERROR(
                'No OpenEdXInstances exist with an external or internal '
                'domain of {domain_names}'.format(
                    domain_names=', '.join(domain_names)
                )
            ))
            sys.exit(1)

        return instances

    def get_instance_metadata(self, instances):
        """ Get a mapping of name_prefix to public_ip for active appservers """
        instance_metadata = {}
        for instance in instances:
            appserver = instance.get_active_appservers().first()
            name_prefix = appserver.server_name_prefix
            domain = instance.domain
            ref_name = instance.ref.name
            external_lms_domain = instance.external_lms_domain or 'N/A'

            try:
                betatestapplication = instance.betatestapplication.get()
                email = betatestapplication.user.email
                status = betatestapplication.status
            except BetaTestApplication.DoesNotExist:
                email = 'N/A'
                status = 'N/A'

            instance_metadata[name_prefix] = {
                'domain': domain,
                'ref_name': ref_name,
                'name_prefix': name_prefix,
                'public_ip': appserver.server.public_ip,
                'instance_age': datetime.now(instance.created.tzinfo) - instance.created,
                'email': email,
                'status': status,
                'external_lms_domain': external_lms_domain,
            }

        return instance_metadata

    def get_elasticsearch_hits_data_summary(self, playbook_output_dir, name_prefixes, start_date, end_date):
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

        self.stderr.write(self.style.SUCCESS(','.join(name_prefixes)))

        # Launch the collect_elasticsearch_data playbook, which places a file into the `playbook_output_dir`
        # on this host.
        ansible.capture_playbook_output(
            requirements_path=os.path.join(
                os.path.dirname(playbook_path),
                'requirements.txt'
            ),
            inventory_str=inventory,
            vars_str=(
                'elasticsearch_host: {elasticsearch_host}\n'
                'elasticsearch_port: {elasticsearch_port}\n'
                'elasticsearch_username: {elasticsearch_username}\n'
                'elasticsearch_password: {elasticsearch_password}\n'
                'elasticsearch_use_ssl: {elasticsearch_use_ssl}\n'
                'elasticsearch_ca_cert: "{elasticsearch_ca_cert}"\n'
                'local_output_dir: {output_dir}\n'
                'remote_output_filename: /tmp/elasticsearch_activity_report\n'
                'server_name_prefixes: {server_name_prefixes}\n'
                'start_date: {start_date}\n'
                'end_date: {end_date}'
            ).format(
                elasticsearch_host=settings.INSTANCE_LOGS_SERVER_ELASTICSEARCH_HOST,
                elasticsearch_port=settings.INSTANCE_LOGS_SERVER_ELASTICSEARCH_PORT,
                elasticsearch_username=settings.INSTANCE_LOGS_SERVER_ELASTICSEARCH_USERNAME,
                elasticsearch_password=settings.INSTANCE_LOGS_SERVER_ELASTICSEARCH_PASSWORD,
                elasticsearch_use_ssl=settings.INSTANCE_LOGS_SERVER_ELASTICSEARCH_USE_SSL,
                elasticsearch_ca_cert=settings.INSTANCE_LOGS_SERVER_ELASTICSEARCH_CA_CERT.replace('\n', '\\n'),
                output_dir=playbook_output_dir,
                server_name_prefixes=','.join(name_prefixes),
                start_date=start_date,
                end_date=end_date
            ),
            playbook_path=playbook_path,
            username=settings.INSTANCE_LOGS_SERVER_SSH_USERNAME,
            logger_=log_line,
        )

    def get_instance_usage_data(self, playbook_output_dir, instance_metadata, start_date, end_date):
        """ Execute the collect_activity playbook to gather statistics """
        inventory = '[apps]'
        for name_prefix, metadata in instance_metadata.items():
            inventory += (
                '\n{server} '
                'config_section={name_prefix} '
                'local_output_filename={name_prefix}_user_statistics'
            ).format(
                name_prefix=name_prefix,
                server=metadata['public_ip'],
            )

        self.stderr.write(self.style.SUCCESS(inventory))

        playbook_path = os.path.join(
            settings.SITE_ROOT,
            'playbooks/collect_activity/collect_activity.yml'
        )

        def log_line(line):
            """Helper to pass to capture_playbook_output()."""
            self.stderr.write(self.style.SUCCESS(line))
        log_line.info = log_line
        log_line.error = log_line

        playbook_extra_script_arguments = f'--start-date {start_date} --end-date {end_date}'
        if settings.INSTANCE_LOGS_SERVER_HOST:
            playbook_extra_script_arguments += ' --skip-hit-statistics'

        # Launch the collect_activity playbook, which places a file into the `playbook_output_dir`
        # on this host.
        ansible.capture_playbook_output(
            requirements_path=os.path.join(os.path.dirname(playbook_path), 'requirements.txt'),
            inventory_str=inventory,
            vars_str=(
                'local_output_dir: {output_dir}\n'
                'remote_output_filename: /tmp/activity_report\n'
                'extra_script_arguments: {extra_script_arguments}\n'
            ).format(
                output_dir=playbook_output_dir,
                extra_script_arguments=playbook_extra_script_arguments
            ),
            playbook_path=playbook_path,
            username=settings.INSTANCE_LOGS_SERVER_SSH_USERNAME,
            logger_=log_line,
        )

    def collect_instance_statistics(
            self,
            out,
            domain_names,
            start_date,
            end_date
    ):
        """Generate the instance statistics CSV."""
        instances = self.get_instances_from_domain_names(domain_names)
        instance_metadata = self.get_instance_metadata(instances)

        self.stderr.write(self.style.SUCCESS('Running playbook...'))

        with ansible.create_temp_dir() as playbook_output_dir:
            self.get_elasticsearch_hits_data_summary(
                playbook_output_dir,
                instance_metadata.keys(),
                start_date,
                end_date
            )
            self.get_instance_usage_data(
                playbook_output_dir,
                instance_metadata,
                start_date,
                end_date
            )

            csv_writer = csv.writer(out, quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writerow([
                'Fully Qualified Domain Name',
                'Name',
                'Contact Email',
                'Status',
                'Unique Hits',
                'Total Hits',
                'Total Courses',
                'Total Users',
                'Active Users',
                'Age (Days)',
                'Custom External Domain',
            ])

            filenames = [os.path.join(playbook_output_dir, f) for f in os.listdir(playbook_output_dir)]
            playbook_data = ConfigParser()
            playbook_data.read(filenames)

            for name_prefix, metadata in instance_metadata.items():
                try:
                    section = playbook_data[name_prefix]
                except KeyError:
                    # Set the section to an empty dict
                    section = {}

                csv_writer.writerow([
                    metadata['domain'],
                    metadata['ref_name'],
                    metadata['email'],
                    metadata['status'],
                    section.get('unique_hits', 'N/A'),
                    section.get('total_hits', 'N/A'),
                    section.get('courses', 'N/A'),
                    section.get('users', 'N/A'),
                    section.get('active_users', 'N/A'),
                    metadata['instance_age'],
                    metadata['external_lms_domain']
                ])

        self.stderr.write(self.style.SUCCESS('Done generating CSV output.'))
