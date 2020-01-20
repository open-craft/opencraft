# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
import os
import time
import xmlrpc.client

import requests
from django.conf import settings
from django.core.cache import cache
from lexicon.config import ConfigResolver
from lexicon.client import Client


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Classes #####################################################################

class GandiAPI():
    """
    Gandi API proxy object
    """

    def __init__(self, api_url='https://rpc.gandi.net/xmlrpc/', client=None):
        # This is a map of domain_name => zone_id key-value pairs.
        self._zone_id_cache = None
        if client:
            self.client = client
        else:
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

    def _populate_zone_id_cache(self):
        """
        Populate the internal zone ID cache with all domains in the current Gandi account.
        """
        self._zone_id_cache = {}
        for domain_dict in self.client.domain.list(self.api_key):
            domain = domain_dict['fqdn'].lower()
            self._zone_id_cache[domain] = self.client.domain.info(self.api_key, domain)['zone_id']

    def split_domain_name(self, domain):
        """
        Split the given domain name in the registered domain and the subdomain.
        """
        if self._zone_id_cache is None:
            self._populate_zone_id_cache()
        labels = domain.lower().split('.')
        for split_index in range(len(labels) - 1):
            registered_domain = '.'.join(labels[split_index:])
            if registered_domain in self._zone_id_cache:
                subdomain = '.'.join(labels[:split_index]) or '@'
                return subdomain, registered_domain
        raise ValueError(
            'The given domain name "{}" does not match any domain registered in the Gandi account.'.format(domain)
        )

    def get_zone_id(self, domain):
        """
        Gandi zone ID used by domain
        """
        if self._zone_id_cache is None:
            self._populate_zone_id_cache()
        return self._zone_id_cache[domain]

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
                except (xmlrpc.client.Fault, TimeoutError):
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
        assert 'name' not in record, 'The name gets extracted from the FQDN passed in `domain`.'
        record['name'], registered_domain = self.split_domain_name(domain)

        def set_dns_record_callback(zone_id, zone_version):
            """
            Callback to be passed to _dns_operation().
            """
            self.delete_dns_record(zone_id, zone_version, record['name'])
            return self.add_dns_record(zone_id, zone_version, record)

        self._dns_operation(
            callback=set_dns_record_callback,
            domain=registered_domain,
            log_msg='Setting DNS record: {}'.format(record),
        )

    def remove_dns_record(self, domain):
        """
        Remove the given name for the domain.
        """
        subdomain, registered_domain = self.split_domain_name(domain)

        def remove_dns_record_callback(zone_id, zone_version):
            """
            Callback to be passed to _dns_operation().
            """
            self.delete_dns_record(zone_id, zone_version, subdomain)

        self._dns_operation(
            callback=remove_dns_record_callback,
            domain=registered_domain,
            log_msg='Deleting DNS record: {}'.format(subdomain),
        )


class GandiV5API:
    """
    Gandi v5 LiveDNS API client
    """
    def __init__(self, api_key, api_base='https://dns.api.gandi.net/api/v5'):
        self.api_base = api_base
        self.api_key = api_key
        self._domain_cache = None

    def _populate_domain_cache(self):
        """
        Populate the internal domain cache with all domains in the current Gandi account.
        """
        self._domain_cache = []
        domains_api_url = '{}/domains'.format(self.api_base)

        try:
            response = requests.get(domains_api_url, headers={'X-Api-Key': self.api_key})
            response.raise_for_status()
            domains = response.json()
            self._domain_cache = [domain['fqdn'] for domain in domains]
        except requests.RequestException:
            logger.error('Unable to retrieve the domains in the given account.')

        if not self._domain_cache:
            logger.warning(
                'Using the default instance base domain %s as the fallback. '
                'This will not work if the API key has no permission to manage the DNS records for this domain',
                settings.GANDI_DEFAULT_BASE_DOMAIN
            )
            self._domain_cache = [settings.GANDI_DEFAULT_BASE_DOMAIN]

    def _split_domain_name(self, domain):
        """
        Split the given domain name to the registered domain and the subdomain.
        """
        if self._domain_cache is None:
            self._populate_domain_cache()
        labels = domain.lower().split('.')
        for split_index in range(len(labels) - 1):
            registered_domain = '.'.join(labels[split_index:])
            if registered_domain in self._domain_cache:
                subdomain = '.'.join(labels[:split_index]) or '@'
                return subdomain, registered_domain
        raise ValueError(
            'The given domain name "{}" does not match any domain registered in the Gandi account.'.format(domain)
        )

    def _get_base_config(self):
        """
        Return the common base configuration for all DNS operation API calls.
        """
        return {
            "provider_name": "gandi",
            "gandi": {
                "auth_token": self.api_key,
                "api_protocol": "rest"
            }
        }

    def _dns_operation(self, callback, log_msg, attempts=4, retry_delay=1):
        """
        Encapsulate logic that is common to high-level DNS operations: grab the global lock, do the operation,
        and retry the whole procedure multiple times if necessary.
        """
        with cache.lock('gandi_set_dns_record'):  # Only do one DNS update at a time
            for i in range(1, attempts + 1):
                try:
                    logger.info('%s (attempt %d out %d)', log_msg, i, attempts)
                    result = callback()
                    break
                except Exception:  # pylint: disable=broad-except
                    if i == attempts:
                        raise
                    time.sleep(retry_delay)
                    retry_delay *= 2
        return result

    def add_dns_record(self, record):
        """
        Add a DNS record to the domain.
        """
        lexicon_config = self._get_base_config()
        lexicon_config['domain'] = record['domain']
        lexicon_config['action'] = 'create'
        lexicon_config['type'] = record['type']
        lexicon_config['name'] = record['name']
        lexicon_config['content'] = record['value']
        lexicon_config['ttl'] = record['ttl']
        config = ConfigResolver()
        config.with_dict(dict_object=lexicon_config)
        client = Client(config)
        result = client.execute()
        return result

    def set_dns_record(self, domain, **record):
        """
        Set a DNS record. This method takes the mandatory 'domain' parameter to be able to support multiple domains
        handled by the same Gandi account
        """
        if 'ttl' not in record.keys():
            record['ttl'] = 1200
            assert 'name' not in record, 'The name gets extracted from the FQDN passed in `domain`'
        record['name'], record['domain'] = self._split_domain_name(domain)

        def set_dns_record_callback():
            """
            Callback to be passed to _dns_operation()
            """
            self.delete_dns_record(record)
            self.add_dns_record(record)

        self._dns_operation(
            callback=set_dns_record_callback,
            log_msg='Setting DNS record: {}'.format(record),
        )

    def delete_dns_record(self, record):
        """
        Delete a record from the domain.
        """
        lexicon_config = self._get_base_config()
        lexicon_config['domain'] = record['domain']
        lexicon_config['action'] = 'delete'
        lexicon_config['name'] = record['name']
        lexicon_config['type'] = record['type']
        config = ConfigResolver()
        config.with_dict(dict_object=lexicon_config)
        client = Client(config)
        try:
            result = client.execute()
        except Exception as e:  # pylint: disable=broad-except
            # This ugly checking of the exception message is needed
            # as the library only throws an instance of the Exception class.
            if 'Record identifier could not be found' in str(e):
                result = True
        return result

    def remove_dns_record(self, domain, **record):
        """
        Remove the given name for the domain.
        """
        record['name'], record['domain'] = self._split_domain_name(domain)

        def remove_dns_record_callback():
            self.delete_dns_record(record)

        self._dns_operation(
            callback=remove_dns_record_callback,
            log_msg='Deleting DNS record: {}'.format(record),
        )


try:
    api = GandiV5API(settings.GANDI_API_KEY)
except Exception:  # pylint: disable=broad-except
    api = GandiV5API(os.environ['GANDI_API_KEY'])
