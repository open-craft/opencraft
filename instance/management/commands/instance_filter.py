# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
Instance app - Instance filter management command, shared by other commands
"""

# Imports #####################################################################

import time
import logging

from django.core.management.base import BaseCommand

from instance.ansible import load_yaml
from instance.models.openedx_instance import OpenEdXInstance

LOG = logging.getLogger(__name__)

# Classes #####################################################################


class Command(BaseCommand):
    """
    instance_filter management command class
    """
    help = (
        'Presents a list of instances based on the given arguments.'
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.options = {}
        self.retried = {}

    def add_arguments(self, parser):
        """
        Add named arguments.
        """
        parser.add_argument(
            '--filter',
            type=load_yaml,
            default='{}',
            help='YAML containing the OpenEdXInstance queryset filter to use to select the instances to use.'
                 ' Pass @path/to/file.yml to read filters from a file. '
                 ' Note that archived instances are automatically excluded. Omit to include all un-archived instances.'
        )
        parser.add_argument(
            '--exclude',
            type=load_yaml,
            default='{}',
            help='YAML containing the OpenEdXInstance exclusion queryset used to exclude instances. '
                 'Pass @path/to/file.yml to read exclusions from a file. '
        )

    def handle(self, *args, **options):
        """
        List filtered instances
        """
        self.options = options
        self.log_instances(self.get_instances())

    def get_instances(self):
        """
        Return a queryset containing the instances selected by the `filter` and `exclude` options,
        and exclude all archived instances.
        """
        instance_filter = self.options.get('filter', {})
        instance_exclusion = self.options.get('exclude', {})
        return OpenEdXInstance.objects.filter(
            **instance_filter
        ).exclude(
            **instance_exclusion
        ).exclude(
            ref_set__is_archived=True
        )

    def log_instances(self, instances):
        """
        Log details about each instance filtered (omitting excluded and archived).
        """
        for instance in instances.all():
            LOG.info(instance)
