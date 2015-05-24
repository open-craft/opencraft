# -*- encoding: utf-8 -*-
#
# Copyright (c) 2015, OpenCraft
#

# Imports #####################################################################

from pprint import pprint

from django.conf import settings
from huey.djhuey import task

from .ansible import run_ansible_playbook, get_inventory_str, get_vars_str
from .gandi import GandiAPI
from .openstack import create_sandbox_server, get_nova_client, get_server_public_ip, sleep_until_port_open


# Tasks #######################################################################

@task()
def create_sandbox_instance(subdomain, instance_name):
    nova = get_nova_client()
    gandi = GandiAPI()

    # Create server
    server = create_sandbox_server(nova, subdomain)

    # Update DNS
    server_ip = get_server_public_ip(server)
    gandi.set_dns_record(type='A', name=subdomain, value=server_ip)

    # Run ansible sandbox playbook
    sleep_until_port_open(server_ip, 22)
    log_lines = []
    with run_ansible_playbook(
        get_inventory_str(server_ip),
        get_vars_str(
            instance_name,
            '{}.{}'.format(subdomain, settings.INSTANCES_BASE_DOMAIN)),
        'edx_sandbox.yml',
        username='admin',
    ) as processus:
        for line in processus.stdout:
            line = line.rstrip()
            log_lines.append(line)
            pprint(line)

    return log_lines
