# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

# Load django environment #####################################################

import os
import sys
import django
sys.path.append('/home/antoviaque/prog/opencraft')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opencraft.dev")
django.setup()


# Imports #####################################################################

import socket
import time

from pprint import pprint
from novaclient.v2.client import Client as NovaClient

from django.conf import settings

from instance.gandi import GandiAPI
from ansible import run_ansible_playbook, get_inventory_str, get_vars_str


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

    pprint('Creating server "{}":\n\t- Image: {}\n\t- Flavor: {}'.format(server_name, image, flavor))
    return nova.servers.create(server_name, image, flavor, key_name=key_name)


def delete_servers_by_name(nova, server_name):
    for server in nova.servers.list():
        if server.name == server_name:
            pprint('deleting server {}'.format(server))
            nova.servers.delete(server)


def sleep_until_loaded(nova, server):
    pprint('Waiting for server {server} to start...'.format(server=server))
    while True:
        # TODO: Add timeout & error handling instance startup
        if server._loaded and server.status == 'ACTIVE': #pylint: disable=protected-access
            break

        time.sleep(1)

        # Refresh server status
        server = nova.servers.get(server)

    return server


def sleep_until_port_open(ip, port):
    pprint('Waiting for port {port} to open on {ip}...'.format(port=port, ip=ip))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while sock.connect_ex((ip, port)) != 0:
        time.sleep(1)


def get_server_public_address(server):
    addresses = server.addresses

    # TODO: Ensure it is public
    first_address_key = list(addresses.keys())[0]
    first_address = addresses[first_address_key][0]

    return first_address


def get_server_public_ip(server):
    return get_server_public_address(server)['addr']


def create_sandbox_server(nova, server_name):
    delete_servers_by_name(nova, server_name)
    server = create_server(nova,
        server_name,
        settings.OPENSTACK_SANDBOX_FLAVOR,
        settings.OPENSTACK_SANDBOX_BASE_IMAGE,
        key_name='antoviaque', # TODO Create the key dynamically
    )
    server = sleep_until_loaded(nova, server)

    return server


# Main ########################################################################

def main():
    nova = get_nova_client()
    gandi = GandiAPI()

    # Create server
    server_name = 'sandbox4'
    server = create_sandbox_server(nova, server_name)

    # Update DNS
    server_ip = get_server_public_ip(server)
    gandi.set_dns_record(type='A', name=server_name, value=server_ip)

    # Run ansible
    sleep_until_port_open(server_ip, 22)
    with run_ansible_playbook(
        get_inventory_str(server_ip),
        get_vars_str(
            'OpenCraft {}'.format(server_name),
            '{}.openedxhosting.com'.format(server_name)),
        'edx_sandbox.yml',
        username='admin',
    ) as processus:
        for line in processus.stdout:
            pprint(line.rstrip())

if __name__ == "__main__":
    main()
