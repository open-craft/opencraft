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
Management command to clean up any OpenStack VMs that are known to be dead, but
evidently are still running about.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from instance import openstack_utils
from instance.models.server import OpenStackServer, Status


class Command(BaseCommand):
    """
    kill_zombies management command class
    """
    help = "Cleans up any OpenStack VMs that are on record as being terminated, but are evidently still running."

    def __init__(self):
        super().__init__()
        self.region = None
        self.dry_run = False

    def add_arguments(self, parser):
        """
        Add named arguments.
        """
        parser.add_argument(
            "--region",
            type=str,
            required=True,
            help="The OpenStack region against which to run this command."
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Runs without actually making any changes."
        )

    def handle(self, *args, **options):
        """
        Finds zombies and kills them.
        """
        self.log("Starting kill_zombies")

        # Set options
        self.region = options.get("region")
        self.dry_run = options.get("dry_run", False)

        # Start nova up and get the list of servers
        nova = openstack_utils.get_nova_client(self.region)
        nova_servers = nova.servers.list()

        if not nova_servers:
            self.log('No servers found in region {}.'.format(self.region))
            return
        self.log('Found {} unterminated servers in region {}.'.format(len(nova_servers), self.region))

        # Scan each server for the zombieness.
        death_count = sum(1 for srv in nova_servers if self.not_zombie_or_die(srv))

        if self.dry_run:
            self.log("Would have terminated {} zombies if this weren't a dry run.".format(death_count))
        else:
            self.log("Terminated {} zombies.".format(death_count))

    def not_zombie_or_die(self, nova_server):
        """
        Checks if a server is a zombie, and if it is (and only if it is!),
        terminate it.
        """
        self.log("Scanning server {} with status {}...".format(nova_server.name, nova_server.status))

        # Detect whether the server name matches Ocim rules.
        server = self.find_openstack_server(nova_server.name)

        # Ignore servers that don't match.
        if not server:
            self.log("Unknown server {}.  Ignoring.".format(nova_server.name))
            return False

        # Only terminate the server if it's already expected to be dead.
        if server.status != Status.Terminated:
            self.log("Server {} is {}.  Ignoring.".format(nova_server.name, server.status))
            return False

        # At this point we're ready to kill the zombie.
        self.log("Terminating zombie server {}.".format(nova_server.name))
        if not self.dry_run:
            try:
                nova_server.delete()
            except Exception as e:  # pylint: disable=broad-except
                self.log("WARNING: Unable to delete server. Error: {}.".format(e))

        return True

    def find_openstack_server(self, server_name):
        """
        Finds and returns the Ocim OpenStack server corresponding to the Nova server name.
        """
        server = None
        server_name_components = server_name.split("-")
        server_id = server_name_components[-1]
        if server_id.isdigit():
            try:
                server = OpenStackServer.objects.get(id=server_id)
            except OpenStackServer.DoesNotExist:
                pass

        # To be doubly sure we're dealing with the right server, match
        # against the name prefix as well.
        if server:
            server_name_prefix = "-".join(server_name_components[:-1])
            if server.name_prefix != server_name_prefix:
                server = None

        return server

    def log(self, message):
        """
        Shortcut to log messages with date and time
        """
        self.stdout.write('{} | {}'.format(
            timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            message
        ))
