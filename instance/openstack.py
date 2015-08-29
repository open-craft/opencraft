# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
OpenStack - Helper functions
"""

# Imports #####################################################################

import json

from django.conf import settings

from instance import utils


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Functions ###################################################################

class OpenStackClient:
    """
    OpenStack CLI wrapper, with proper credentials set in env
    """
    def __init__(self, cluster_name='default'):
        self.env = settings.OPENSTACK_CLUSTER[cluster_name]

    def sh(self, command): #pylint: disable=invalid-name
        """
        Run shell command in subprocess, with the right environment variables for credentials

        Returns the command output in ascii
        """
        return utils.sh(command, env=self.env)

    def run(self, command):
        """
        Run the shell command in a subprocess, requesting the output as JSON

        Returns the JSON output loaded as Python objects
        """
        json_output = self.sh(command + ' -f json')
        return json.loads(json_output)

    def create_server(self, server_name, flavor_selector, image_selector, key_name=None):
        """
        Create a VM via nova
        """
        flavor = nova.flavors.find(**flavor_selector)
        image = nova.images.find(**image_selector)

        logger.info('Creating OpenStack server: name=%s image=%s flavor=%s', server_name, image, flavor)
        return nova.servers.create(server_name, image, flavor, key_name=key_name)

    def delete_servers_by_name(nova, server_name):
        """
        Delete all servers with `server_name`
        """
        for server in nova.servers.list():
            if server.name == server_name:
                logger.info('deleting server %s', server)
                nova.servers.delete(server)


def get_server_public_address(server):
    """
    Retrieve the public IP of `server`
    """
    addresses = server.addresses
    if not addresses:
        return None

    # TODO: Ensure it is public
    first_address_key = list(addresses.keys())[0]
    first_address = addresses[first_address_key][0]

    return first_address
