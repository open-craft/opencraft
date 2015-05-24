# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

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

    # TODO: Ensure it is public
    first_address_key = list(addresses.keys())[0]
    first_address = addresses[first_address_key][0]

    return first_address
