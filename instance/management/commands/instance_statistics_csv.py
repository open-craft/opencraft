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

from configparser import ConfigParser
import csv
from datetime import datetime
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from instance import ansible
from instance.models.openedx_instance import OpenEdXInstance
from registration.models import BetaTestApplication


# Classes #####################################################################


class Command(BaseCommand):
    """
    Logs_activity_csv management command class
    """
    help = (
        'Generates a CSV containing basic activity information about all app servers'
        ' (numbers for hits, distinct hits, users, and courses).'
    )

    LOGS_SERVER = 'logs.opencraft.com'

    def add_arguments(self, parser):
        parser.add_argument(
            '--qualified-domain',
            '-q',
            default=None,
            help='The fully qualified domain name to filter results by',
            required=True
        )
        parser.add_argument(
            '--days',
            '-d',
            default=30,
            help='The number of days that should be queried for statistics. Default is 30 days'
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
                    'Permission denied while attempting to write file: {outfile}'.format(outfile=options['out'])
                ))
                sys.exit(1)

        self.collect_instance_statistics(out, options['qualified_domain'], options['days'])

    def get_instance_from_qualified_domain(self, qualified_domain):
        try:
            instance = OpenEdXInstance.objects.get(
                Q(external_lms_domain=qualified_domain) | Q(internal_lms_domain=qualified_domain)
            )
        except OpenEdXInstance.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                'No OpenEdXInstance exists with an external or internal domain of {qualified_domain}'.format(qualified_domain=qualified_domain)
            ))
            sys.exit(1)

        # If there are no active appservers for the instance, we should error out
        if not instance.successfully_provisioned or not instance.get_active_appservers():
            self.stderr.write(self.style.ERROR(
                'No active OpenEdXAppServers exist for the instance with external or internal domain of {qualified_domain}'.format(qualified_domain=qualified_domain)
            ))
            sys.exit(1)

        return instance

    def get_elasticsearch_statistics(playbook_output_dir, name_prefix, num_days):
        inventory = '[apps]\n{server}'.format(server=self.LOGS_SERVER)
        playbook_path = os.path.join(settings.SITE_ROOT, 'playbooks/collect_instance_statistics/collect_elasticsearch_data.yml')

        def log_line(line):
            """Helper to pass to capture_playbook_output()."""
            self.stderr.write(self.style.SUCCESS(line))
        log_line.info = log_line
        log_line.error = log_line

        # Launch the collect_elasticsearch_data playbook, which places a file into the `playbook_output_dir`
        # on this host.
        ansible.capture_playbook_output(
            requirements_path=os.path.join(os.path.dirname(playbook_path), 'requirements.txt'),
            inventory_str=inventory,
            vars_str=(
                'local_output_dir: {output_dir}\n'
                'remote_output_filename: /tmp/activity_report\n'
                'server_name_prefix: {server_name_prefix}\n'
                'num_days: {num_days}'
            ).format(
                output_dir=playbook_output_dir,
                server_name_prefix=name_prefix,
                num_days=num_days
            ),
            playbook_path=playbook_path,
            username=settings.OPENSTACK_LOGS_SERVER_SSH_USERNAME,
            logger_=log_line,
        )

    def get_appserver_statistics(playbook_output_dir, name_prefix, public_ip):
        inventory = '[apps]\n{server}'.format(server=public_ip)
        playbook_path = os.path.join(settings.SITE_ROOT, 'playbooks/collect_instance_statistics/collect_appserver_data.yml')

        def log_line(line):
            """Helper to pass to capture_playbook_output()."""
            self.stderr.write(self.style.SUCCESS(line))
        log_line.info = log_line
        log_line.error = log_line

        # Launch the collect_appserver_data playbook, which places a file into the `playbook_output_dir`
        # on this host.
        ansible.capture_playbook_output(
            requirements_path=os.path.join(os.path.dirname(playbook_path), 'requirements.txt'),
            inventory_str=inventory,
            vars_str=(
                'local_output_dir: {output_dir}\n'
                'remote_output_filename: /tmp/activity_report\n'
                'server_name_prefix: {server_name_prefix}'
            ).format(
                output_dir=playbook_output_dir,
                server_name_prefix=name_prefix
            ),
            playbook_path=playbook_path,
            username=settings.OPENSTACK_SANDBOX_SSH_USERNAME,
            logger_=log_line,
        )

    def collect_instance_statistics(self, out, qualified_domain, num_days):  # pylint: disable=too-many-locals
        """Generate the activity CSV."""
        instance = self.get_instance_from_qualified_domain(qualified_domain)
        appserver = instance.get_active_appservers().first()
        name_prefix = appserver.server_name_prefix

        self.stderr.write(self.style.SUCCESS('Running playbook...'))

        with ansible.create_temp_dir() as playbook_output_dir:
            get_elasticsearch_statistics(playbook_output_dir, name_prefix, num_days)
            get_appserver_statistics(playbook_output_dir, name_prefix, appserver.server.public_ip)

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
