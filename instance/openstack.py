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

import requests

from novaclient.v2.client import Client as NovaClient

from django.conf import settings

from instance.utils import get_requests_retry


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Functions ###################################################################

def get_nova_client():
    """
    Instanciate a python novaclient.Client() object with proper credentials
    """
    nova = NovaClient(
        settings.OPENSTACK_USER,
        settings.OPENSTACK_PASSWORD,
        settings.OPENSTACK_TENANT,
        settings.OPENSTACK_AUTH_URL,
        region_name=settings.OPENSTACK_REGION,
    )

    # API queries via the nova client occasionally get connection errors from the OpenStack provider.
    # To gracefully recover when the unavailability is short-lived, ensure safe requests (as per
    # urllib3's definition) are retried before giving up.
    adapter = requests.adapters.HTTPAdapter(max_retries=get_requests_retry())
    nova.client.open_session()
    nova.client._session.mount('http://', adapter)
    nova.client._session.mount('https://', adapter)

    return nova


def create_server(nova, server_name, flavor_selector, image_selector, key_name=None):
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
