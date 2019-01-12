# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
Instance app - Archive one or more instances by their domains
"""

# Imports #####################################################################

import logging

from django.core.management.base import BaseCommand

from instance.models.openedx_instance import OpenEdXInstance

LOG = logging.getLogger(__name__)

# Classes #####################################################################


class Command(BaseCommand):
    """
    archive_instances management command class
    """
    help = 'Archive instances specified by their internal LMS domain.'

    def add_arguments(self, parser):
        """
        Add mutually exclusive required arguments --domains and --file to parser.
        """
        domains_source_group = parser.add_mutually_exclusive_group(required=True)
        domains_source_group.add_argument(
            '--domains', help='Comma-separated list of domains'
        )
        domains_source_group.add_argument(
            '--file', help='File containing newline-separated list of instance domains'
        )

    def handle(self, *args, **options):
        """
        Archive instances from a list of domains or from a file.
        """
        domains = options['domains']
        infile = options['file']

        if infile:
            with open(infile, 'r') as f:
                domains = [line.strip() for line in f.readlines()]
        else:
            domains = domains.split(',')

        instances = OpenEdXInstance.objects.filter(
            internal_lms_domain__in=domains,
            ref_set__is_archived=False
        )
        instance_count = instances.count()
        domains_count = len(domains)

        if instance_count == 0:
            self.stdout.write('No unarchived instances found (from %s domains).' % domains_count)
            return

        self.stdout.write('Found %s instances (from %s domains) to be archived...' % (instance_count, domains_count))
        for instance in instances:
            self.stdout.write('- %s' % instance.internal_lms_domain)
        if self.confirm():
            for instance in instances:
                self.stdout.write('Archiving %s...' % instance.internal_lms_domain)
                self.archive_instance(instance)
            self.stdout.write(
                self.style.SUCCESS('Archived %s instances (from %s domains).' % (instance_count, domains_count))
            )
        else:
            self.stdout.write('Cancelled')

    @staticmethod
    def archive_instance(instance):
        """
        Archive a single OpenEdXInstance.
        """
        instance.archive()
        instance.deprovision_rabbitmq()

    def confirm(self):
        """
        Confirm with the user that archiving should proceed.
        """
        self.stdout.write('Are you sure you want to continue? [yes/No]')
        answer = input()
        return answer.lower().startswith('y')
