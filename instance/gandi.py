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
Gandi DNS - Helper functions
"""

# Imports #####################################################################

import logging
import time
import xmlrpc.client

from django.conf import settings
from django.core.cache import cache


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Classes #####################################################################

class GandiAPI():
    """
    Gandi API proxy object
    """
    def __init__(self, api_url='https://rpc.gandi.net/xmlrpc/'):
        self.client = xmlrpc.client.ServerProxy(api_url)

    @property
    def api_key(self):
        """
        Gandi API key
        """
        return settings.GANDI_API_KEY

    @property
    def zone_id(self):
        """
        Gandi Zone ID of the domain
        """
        return settings.GANDI_ZONE_ID

    @property
    def client_zone(self):
        """
        Client domain zone API endpoint
        """
        return self.client.domain.zone

    def delete_dns_record(self, zone_version_id, record_name):
        """
        Delete a record from a version of the domain
        """
        self.client_zone.record.delete(self.api_key, self.zone_id, zone_version_id, {
            'type': ['A', 'CNAME'],
            'name': record_name,
        })

    def add_dns_record(self, zone_version_id, record):
        """
        Add a DNS record to a version of the domain
        """
        return self.client_zone.record.add(self.api_key, self.zone_id, zone_version_id, record)

    def create_new_zone_version(self):
        """
        Create a new version of the domain, based on the current version
        Returns the `version_id` of the version
        """
        return self.client_zone.version.new(self.api_key, self.zone_id)

    def set_zone_version(self, zone_version_id):
        """
        Get a version of the domain per id
        """
        return self.client_zone.version.set(self.api_key, self.zone_id, zone_version_id)

    def set_dns_record(self, attempts=4, retry_delay=1, **record):
        """
        Set a DNS record - Automatically create a new version, update with the change & activate
        """
        if 'ttl' not in record.keys():
            record['ttl'] = 1200

        with cache.lock('gandi_set_dns_record'): # Only do one DNS update at a time
            for i in range(1, attempts + 1):
                try:
                    logger.info('Setting DNS record: %s (attempt %d out of %d)', record, i, attempts)
                    new_zone_version = self.create_new_zone_version()
                    self.delete_dns_record(new_zone_version, record['name'])
                    returned_record = self.add_dns_record(new_zone_version, record)
                    self.set_zone_version(new_zone_version)
                    break
                except xmlrpc.client.Fault:
                    if i == attempts:
                        raise
                    time.sleep(retry_delay)
                    retry_delay *= 2
        return returned_record
