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
Instance app - instances' metadata update management command
"""

# Imports #####################################################################

import sys

from django.conf import settings
from django.core.management.base import BaseCommand

import consul

from instance.models.openedx_instance import OpenEdXInstance


# Classes #####################################################################


class Command(BaseCommand):
    """
    management command class for updating instances metadata
    """
    help = 'Updates the Consul metadata for all instances or just a single instance.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-clean',
            action='store_true',
            help='Will skip cleaning metadata for archived instances.'
        )
        parser.add_argument(
            '--skip-update',
            action='store_true',
            help='Will skip updating metadata for instances.'
        )

    def handle(self, *args, **options):
        if not settings.CONSUL_ENABLED:
            self.stdout.write(self.style.WARNING(
                'This command does nothing unless you enable Consul in the configuration. Exiting...'
            ))
            sys.exit(0)

        if not options.get('skip_update'):
            self.update_all_instances_metadata()

        if not options.get('skip_clean'):
            self.clean_consul_metadata()

    def update_all_instances_metadata(self):
        """
        This method will iterate over all non-archived instances to update
        their metadata in Consul.
        """
        instances = self.get_running_instances()

        self.stdout.write('Updating {} instances\' metadata...'.format(instances.count()))
        for instance in instances:
            instance.update_consul_metadata()

        self.stdout.write(self.style.SUCCESS('Successfully updated instances\' metadata'))

    def clean_consul_metadata(self):
        """
        This method will iterate over all archived instances and clean their
        metadata from Consul.
        """
        client = consul.Consul()
        instances_ids = self.get_archived_instances()
        self.stdout.write('Cleaning metadata for {} archived instances...'.format(len(instances_ids)))

        for instances_id in instances_ids:
            prefix = settings.CONSUL_PREFIX.format(ocim=settings.OCIM_ID, instance=instances_id)
            client.kv.delete(prefix, recurse=True)
        self.stdout.write(self.style.SUCCESS('Successfully cleaned archived instances\' metadata'))

    @staticmethod
    def get_running_instances():
        """
        Generates a queryset of the active instances. Didn't put it as a
        class variable to avoid multiple processes mutations.

        :return: A Queryset of all active OpenEdXInstances
        """
        return OpenEdXInstance.objects.filter(ref_set__is_archived=False)

    def get_archived_instances(self):
        """
        This management command gets the list of instance ids in Consul and the
        non-archived instance ids from the database. Each instance only occurring
        in Consul, but has been archived since should be considered archived.

        :return: A set of all archived OpenEdXInstances
        """
        agent = consul.Consul()
        archived_instances_ids = set()

        instances_prefix = '{ocim}/instances/'.format(ocim=settings.OCIM_ID)
        _, consul_instances_keys = agent.kv.get(instances_prefix, recurse=True, keys=True)

        if not consul_instances_keys:
            self.stdout.write('Consul does not contain data yet')
            return archived_instances_ids

        running_instances = self.get_running_instances()
        running_instances_ids = running_instances.values_list('id', flat=True)

        for key in consul_instances_keys:
            id_elements = key.split('/')
            try:
                instance_id = int(id_elements[2])
            except (IndexError, ValueError):
                self.stdout.write(self.style.WARNING('A Consul key found with an unknown structure: {}'.format(key)))
                continue

            if instance_id not in running_instances_ids:
                archived_instances_ids.add(instance_id)

        return archived_instances_ids
