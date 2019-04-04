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
from unittest import mock
import xmlrpc.client


class FakeZone:
    """
    A fake implementation of a Gandi DNS zone.

    The fake implementation keeps track of version numbers and DNS records.
    """
    def __init__(self):
        self.active_version = 0
        self.next_version = 1
        self.records = {0: []}

    def filter_records(self, version_id, query_record, inverse_match=False):
        """
        Return DNS records matching the query record.

        If inverse_match is True, return non-matching records instead.
        """
        for record in self.records[version_id]:
            match = True
            for key, value in query_record.items():
                if not isinstance(value, list):
                    value = [value]
                if record.get(key) not in value:
                    match = False
                    break
            if match != inverse_match:
                yield record

    def add_record(self, version_id, record):
        """
        Add a DNS record.
        """
        if version_id == self.active_version:
            raise xmlrpc.client.Fault(581030, "Cannot modify the active version.")
        if version_id not in range(self.next_version):
            raise xmlrpc.client.Fault(581042, "No such version.")
        if {"name", "type", "value"} - record.keys():
            raise xmlrpc.client.Fault(581137, "Required parameter missing.")
        if "ttl" not in record:
            record["ttl"] = 10800
        self.records[version_id].append(record)
        return record

    def delete_record(self, version_id, record):
        """
        Delete a DNS record.
        """
        if version_id == self.active_version:
            raise xmlrpc.client.Fault(581030, "Cannot modify the active version.")
        if version_id not in range(self.next_version):
            raise xmlrpc.client.Fault(581042, "No such version.")
        if "name" not in record:
            # The actual API does not enforce this - you can delete all records by specifying an
            # empty record.  In the context of OpenCraft IM, we always want the name to be included.
            raise xmlrpc.client.Fault(581137, "Required parameter missing.")
        new_records = list(self.filter_records(version_id, record, inverse_match=True))
        deleted = len(self.records[version_id]) - len(new_records)
        self.records[version_id] = new_records
        return deleted

    def list_records(self, version_id, record=None):
        """
        List DNS records.
        """
        if version_id not in range(self.next_version):
            raise xmlrpc.client.Fault(581042, "No such version.")
        if not record:
            return self.records[version_id]
        return list(self.filter_records(version_id, record))

    def new_version(self):
        """
        Create a new version of a DNS zone.
        """
        version = self.next_version
        self.records[version] = self.records[self.active_version].copy()
        self.next_version += 1
        return version

    def set_version(self, version_id):
        """
        Make the given DNS zone version active.
        """
        if version_id not in range(self.next_version):
            raise xmlrpc.client.Fault(581042, "No such version.")
        self.active_version = version_id
        return True


class FakeGandiClient:
    """
    Fake implementation of the XML RPC client for the Gandi API.

    The behaviour should reflect how the behaviour of the actual Gandi client.  The fake responses
    are reduced to the fields we need.
    """

    _DOMAINS_BY_ZONE_ID = {
        9900: "test.com",
        1234: "example.com",
        4711: "opencraft.co.uk",
    }

    def __init__(self):
        self.domain = mock.Mock(spec=["list", "info", "zone"])
        self.domain.list.side_effect = self._domain_list
        self.domain.info.side_effect = self._domain_info
        self.domain.zone.record.add.side_effect = self._domain_zone_record_add
        self.domain.zone.record.delete.side_effect = self._domain_zone_record_delete
        self.domain.zone.record.list.side_effect = self._domain_zone_record_list
        self.domain.zone.version.new.side_effect = self._domain_zone_version_new
        self.domain.zone.version.set.side_effect = self._domain_zone_version_set
        self._registry = {zone_id: FakeZone() for zone_id in self._DOMAINS_BY_ZONE_ID}
        self._version_creation_failures = 0
        self.timeout = False

    def make_version_creation_fail(self, times, timeout=False):
        """
        Make the call to domain.zone.version.new fail for the next `times` attempts.
        """
        self._version_creation_failures = times
        self.timeout = timeout

    def list_records(self, domain):
        """
        Convenience method to make listing the records for a domain easier.
        """
        zone_id = self._domain_info(None, domain)["zone_id"]
        zone = self._registry[zone_id]
        return zone.list_records(zone.active_version)

    def _domain_list(self, api_key):
        """
        List domains managed by the account.
        """
        return [{"fqdn": domain} for domain in self._DOMAINS_BY_ZONE_ID.values()]

    def _domain_info(self, api_key, domain):
        """
        Return details for the given domain.
        """
        domain = domain.lower()
        for zone_id, other_domain in self._DOMAINS_BY_ZONE_ID.items():
            if domain == other_domain:
                return {"fqdn": domain, "zone_id": zone_id}
        raise xmlrpc.client.Fault(510042, "Domain '{}' doesn't exist.".format(domain))

    def _get_zone(self, zone_id):
        """
        Retrieve a fake zone from the registry.
        """
        try:
            return self._registry[zone_id]
        except KeyError:
            raise xmlrpc.client.Fault(581042, "No such zone.") from None

    def _domain_zone_record_add(self, api_key, zone_id, zone_version_id, record):
        """
        Add a DNS record.
        """
        zone = self._get_zone(zone_id)
        return zone.add_record(zone_version_id, record)

    def _domain_zone_record_delete(self, api_key, zone_id, zone_version_id, record):
        """
        Delete a DNS record.
        """
        zone = self._get_zone(zone_id)
        return zone.delete_record(zone_version_id, record)

    def _domain_zone_record_list(self, api_key, zone_id, zone_version_id, record=None):
        """
        List DNS records.
        """
        zone = self._get_zone(zone_id)
        return zone.list_records(zone_version_id, record)

    def _domain_zone_version_new(self, api_key, zone_id):
        """
        Create a new version of a DNS zone.
        """
        if self._version_creation_failures:
            self._version_creation_failures -= 1
            if self.timeout:
                raise TimeoutError()
            else:
                raise xmlrpc.client.Fault(581091, "Error")
        zone = self._get_zone(zone_id)
        return zone.new_version()

    def _domain_zone_version_set(self, api_key, zone_id, zone_version_id):
        """
        Make the given DNS zone version active.
        """
        zone = self._get_zone(zone_id)
        return zone.set_version(zone_version_id)
