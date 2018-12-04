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
Instance app - Archive one or more instances by their domains
"""

# Imports #####################################################################

import logging

from django.core.management.base import BaseCommand
from django.core.management import CommandError

from instance.models.openedx_instance import OpenEdXInstance

LOG = logging.getLogger(__name__)

# Classes #####################################################################


class Command(BaseCommand):
    """
    archive_instances management command class
    """
    help = 'Archive instances specified by their internal LMS domain.'

    def add_arguments(self, parser):
        parser.add_argument('domain', nargs='*', help='Instance domain')
        parser.add_argument(
            '--file',
            help='File containing newline-separated list of instance domains')
        parser.add_argument(
            '--force',
            action='store_true',
            help='Pass --force to archive without confirming first.'
        )

    def handle(self, *args, **options):
        domains = options['domain']
        infile = options['file']
        force = options['force']

        if not domains and not infile:
            raise CommandError('Error: either domain or --file are required')

        if infile:
            # if a file is provided, ignore positional arg domains and use the domains in the file
            with open(infile, 'r') as f:
                domains = f.readlines()
                domains = [d.strip() for d in domains]

        instances = OpenEdXInstance.objects.filter(
            internal_lms_domain__in=domains,
            ref_set__is_archived=False
        )
        instance_count = instances.count()

        self.stdout.write('Archiving %s instances...' % instance_count)
        if self.confirm(force):
            for instance in instances:
                self.stdout.write('Archiving %s...' % instance.internal_lms_domain)
                self.archive_instance(instance)
            self.stdout.write(self.style.SUCCESS('Archived %s instances.' % instance_count))
        else:
            self.stdout.write('Cancelled')

    @staticmethod
    def archive_instance(instance):
        """
        Archive a single OpenEdXInstance.
        """
        instance.archive()
        instance.deprovision_rabbitmq()

    def confirm(self, force):
        """
        Confirm with the user that archiving should proceed, unless force is True.
        """
        if force:
            answer = 'yes'
        else:
            self.stdout.write('Are you sure you want to continue? [yes/No]')
            answer = input()

        return answer.lower().startswith('y')
