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

from novaclient.v2.client import Client as NovaClient

from django.conf import settings


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Functions ###################################################################

def get_nova_client():
    """
    Instanciate a python novaclient.Client() object with proper credentials
    """
    return NovaClient(
            settings.OPENSTACK_USER,
            settings.OPENSTACK_PASSWORD,
            settings.OPENSTACK_TENANT,
            settings.OPENSTACK_AUTH_URL,
            region_name=settings.OPENSTACK_REGION,
        )


def create_server(nova, server_name, flavor_selector, image_selector, key_name=None):
    flavor = nova.flavors.find(**flavor_selector)
    image = nova.images.find(**image_selector)

    logger.info('Creating OpenStack server: name=%s image=%s flavor=%s', server_name, image, flavor)
    return nova.servers.create(server_name, image, flavor, key_name=key_name)


def delete_servers_by_name(nova, server_name):
    for server in nova.servers.list():
        if server.name == server_name:
            logger.info('deleting server %s', server)
            nova.servers.delete(server)


def get_server_public_address(server):
    addresses = server.addresses
    if not addresses:
        return None

    # TODO: Ensure it is public
    first_address_key = list(addresses.keys())[0]
    first_address = addresses[first_address_key][0]

    return first_address
