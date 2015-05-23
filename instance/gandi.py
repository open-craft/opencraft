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

from pprint import pprint
import xmlrpc.client

from django.conf import settings


# Classes #####################################################################

class GandiAPI():
    """
    Gandi API proxy object
    """

    def __init__(self):
        self.client = xmlrpc.client.ServerProxy('https://rpc.gandi.net/xmlrpc/')

    @property
    def api_key(self):
        return settings.GANDI_API_KEY

    @property
    def zone_id(self):
        return settings.GANDI_ZONE_ID

    @property
    def client_zone(self):
        return self.client.domain.zone

    def get_dns_records(self):
        return self.client_zone.record.list(self.api_key, self.zone_id, 0)

    def delete_dns_record(self, zone_version_id, record_name):
        self.client_zone.record.delete(self.api_key, self.zone_id, zone_version_id, {
            'type' : ['A', 'CNAME'],
            'name': record_name,
        })

    def add_dns_record(self, zone_version_id, record):
        return self.client_zone.record.add(self.api_key, self.zone_id, zone_version_id, record)

    def create_new_zone_version(self):
        return self.client_zone.version.new(self.api_key, self.zone_id)

    def set_zone_version(self, zone_version_id):
        return self.client_zone.version.set(self.api_key, self.zone_id, zone_version_id)

    def set_dns_record(self, **record):
        if 'ttl' not in record.keys():
            record['ttl'] = 1200

        new_zone_version = self.create_new_zone_version()
        self.delete_dns_record(new_zone_version, record['name'])
        returned_record = self.add_dns_record(new_zone_version, record)
        self.set_zone_version(new_zone_version)
        return returned_record



# Main ########################################################################

if __name__ == "__main__":
    gandi = GandiAPI()

    print('\n== DNS Records =====')
    pprint(gandi.get_dns_records())

    print('\n== Setting record =====')
    pprint(gandi.set_dns_record(type='A', name='sandbox4', value='92.222.80.210'))

    print('\n== DNS Records =====')
    pprint(gandi.get_dns_records())
