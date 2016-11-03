# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
        # This is a map of domain_name => zone_id key-value pairs.
        self._zone_id_cache = {}
        self.client = xmlrpc.client.ServerProxy(api_url)

    @property
    def api_key(self):
        """
        Gandi API key
        """
        return settings.GANDI_API_KEY

    @property
    def client_zone(self):
        """
        Client domain zone API endpoint
        """
        return self.client.domain.zone

    def get_zone_id(self, domain):
        """
        Gandi zone ID used by domain
        """
        zone_id = self._zone_id_cache.get(domain, None)
        if zone_id is None:
            zone_id = self.client.domain.info(self.api_key, domain)['zone_id']
            self._zone_id_cache[domain] = zone_id
        return zone_id

    def delete_dns_record(self, zone_id, zone_version_id, record_name):
        """
        Delete a record from a version of the domain
        """
        self.client_zone.record.delete(self.api_key, zone_id, zone_version_id, {
            'type': ['A', 'CNAME'],
            'name': record_name,
        })

    def add_dns_record(self, zone_id, zone_version_id, record):
        """
        Add a DNS record to a version of the domain
        """
        return self.client_zone.record.add(self.api_key, zone_id, zone_version_id, record)

    def create_new_zone_version(self, zone_id):
        """
        Create a new version of the domain, based on the current version
        Returns the `version_id` of the version
        """
        return self.client_zone.version.new(self.api_key, zone_id)

    def set_zone_version(self, zone_id, zone_version_id):
        """
        Get a version of the domain per id
        """
        return self.client_zone.version.set(self.api_key, zone_id, zone_version_id)

    def _dns_operation(self, callback, domain, log_msg, attempts=4, retry_delay=1):
        """
        Encapsulate logic that is common to high-level DNS operations: grab the global lock, get the
        zone_id for a domain, create a new zone version, activate the zone version after successful
        update, and retry the whole procedure multiple times if necessary.
        """
        with cache.lock('gandi_set_dns_record'): # Only do one DNS update at a time
            for i in range(1, attempts + 1):
                try:
                    logger.info('%s (attempt %d out of %d)', log_msg, i, attempts)
                    zone_id = self.get_zone_id(domain)
                    new_zone_version = self.create_new_zone_version(zone_id)
                    result = callback(zone_id, new_zone_version)
                    self.set_zone_version(zone_id, new_zone_version)
                    break
                except xmlrpc.client.Fault:
                    if i == attempts:
                        raise
                    time.sleep(retry_delay)
                    retry_delay *= 2
        return result

    def set_dns_record(self, domain, **record):
        """
        Set a DNS record. This method takes the mandatory `domain` parameter to be able to support
        multiple domains, handled by the same Gandi account.
        """
        if 'ttl' not in record.keys():
            record['ttl'] = 1200

        def set_dns_record_callback(zone_id, zone_version):
            """
            Callback to be passed to _dns_operation().
            """
            self.delete_dns_record(zone_id, zone_version, record['name'])
            return self.add_dns_record(zone_id, zone_version, record)

        self._dns_operation(
            callback=set_dns_record_callback,
            domain=domain,
            log_msg='Setting DNS record: {}'.format(record),
        )

    def remove_dns_record(self, domain, name):
        """
        Remove the given name for the domain.
        """
        def remove_dns_record_callback(zone_id, zone_version):
            """
            Callback to be passed to _dns_operation().
            """
            self.delete_dns_record(zone_id, zone_version, name)

        self._dns_operation(
            callback=remove_dns_record_callback,
            domain=domain,
            log_msg='Deleting DNS record: {}'.format(name),
        )
