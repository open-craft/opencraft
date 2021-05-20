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
Fake implementation of the XML RPC client for the Gandi API.
"""


class FakeGandiV5APIClient:
    """
    Fake implementation of the Gandi V5 API client.
    """

    def __init__(self):
        self._domains = {
            "test.com": [],
            "example.com": [],
            "opencraft.co.uk": [],
        }

    def _split_domain(self, domain):
        """
        Split a FQDN into the registered domain and its subdomain.
        """
        subdomain = None
        registered_domain = None
        labels = domain.lower().split('.')
        for split_index in range(len(labels) - 1):
            registered_domain = '.'.join(labels[split_index:])
            if registered_domain in self._domains:
                subdomain = '.'.join(labels[:split_index]) or '@'
                break
        return subdomain, registered_domain

    def set_dns_record(self, domain, **record):
        """
        Set the given DNS record for the domain.
        """
        subdomain, registered_domain = self._split_domain(domain)
        record['name'] = subdomain
        if 'ttl' not in record:
            record['ttl'] = 1200
        if registered_domain in self._domains:
            self._domains[registered_domain] = [
                item for item in self._domains[registered_domain] if item['name'] != subdomain
            ]
            self._domains[registered_domain].append(record)

    def remove_dns_record(self, domain, **record):
        """
        Remove the given DNS record for the domain.
        """
        subdomain, registered_domain = self._split_domain(domain)
        if registered_domain in self._domains:
            self._domains[registered_domain] = [
                item for item in self._domains[registered_domain] if item['name'] != subdomain
            ]

    def list_records(self, domain):
        """
        List the DNS records for the given registered domain.
        """
        return self._domains[domain]
