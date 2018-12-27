# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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

from instance import ansible
from instance.models.openedx_appserver import OpenEdXAppServer
from registration.models import BetaTestApplication


# Classes #####################################################################


class Command(BaseCommand):
    """
    Activity_csv management command class
    """
    help = (
        'Generates a CSV containing basic activity information about active app servers'
        ' (numbers for distinct hits, users, and courses).'
    )

    def add_arguments(self, parser):
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

        self.activity_csv(out)

    @staticmethod
    def get_active_appservers():
        """ Produce a mapping of public IPs (of active app servers) to parent instances. """
        active_appservers = {}
        for appserver in OpenEdXAppServer.objects.filter(_is_active=True):
            public_ip = appserver.server.public_ip
            if public_ip is not None:
                active_appservers[public_ip] = appserver.instance
        return active_appservers

    def activity_csv(self, out):
        """Generate the activity CSV."""
        active_appservers = self.get_active_appservers()
        if not active_appservers:
            self.stderr.write(
                self.style.SUCCESS('There are no active app servers! Nothing to do.')
            )
            sys.exit(0)

        self.stderr.write(self.style.SUCCESS('Running playbook...'))

        with ansible.create_temp_dir() as playbook_output_dir:
            inventory = '[apps]\n{servers}'.format(servers='\n'.join(active_appservers.keys()))
            playbook_path = os.path.join(settings.SITE_ROOT, 'playbooks/collect_activity/collect_activity.yml')

            def log_line(line):
                """Helper to pass to capture_playbook_output()."""
                self.stderr.write(self.style.SUCCESS(line))
            log_line.info = log_line
            log_line.error = log_line

            # Launch the collect_activity playbook, which places a set of files into the `playbook_output_dir`
            # on this host.
            ansible.capture_playbook_output(
                requirements_path=os.path.join(os.path.dirname(playbook_path), 'requirements.txt'),
                inventory_str=inventory,
                vars_str=(
                    'local_output_dir: {output_dir}\n'
                    'remote_output_filename: /tmp/activity_report'
                ).format(output_dir=playbook_output_dir),
                playbook_path=playbook_path,
                username=settings.OPENSTACK_SANDBOX_SSH_USERNAME,
                logger_=log_line,
            )

            csv_writer = csv.writer(out, quoting=csv.QUOTE_NONNUMERIC)
            csv_writer.writerow([
                'Appserver IP', 'Internal LMS Domain', 'Name', 'Contact Email', 'Unique Hits', 'Total Users',
                'Total Courses', 'Age (Days)'
            ])

            filenames = [os.path.join(playbook_output_dir, f) for f in os.listdir(playbook_output_dir)]
            data = ConfigParser()
            data.read(filenames)

            for public_ip, instance in sorted(active_appservers.items(), key=lambda tup: tup[1].id):
                try:
                    section = data[public_ip]
                except KeyError:
                    # Fill in stats for any instaces that failed with "N/A"
                    section = {'hits': 'N/A', 'users': 'N/A', 'courses': 'N/A'}

                instance_age = datetime.now(instance.created.tzinfo) - instance.created

                try:
                    email = instance.betatestapplication_set.get().user.email
                except BetaTestApplication.DoesNotExist:
                    email = 'N/A'

                csv_writer.writerow([
                    public_ip, instance.internal_lms_domain, instance.ref.name, email,
                    section['hits'], section['users'], section['courses'],
                    instance_age.days
                ])

            self.stderr.write(self.style.SUCCESS('Done generating CSV output.'))
