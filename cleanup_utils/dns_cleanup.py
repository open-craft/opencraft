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
Gandi DNS Cleanup Script

Cleans up all DNS entries left behind from CI
"""

import logging
import xmlrpc

# Logging #####################################################################

logger = logging.getLogger('integration_cleanup')


# Constants ###################################################################

BATCH_SIZE = 200


# Classes #####################################################################

class DnsCleanupInstance():
    """
    Handles the cleanup of dangling DNS entries
    """
    def __init__(self, zone_id, api_key, dry_run, api_url='https://rpc.gandi.net/xmlrpc/'):
        """
        Set up variables needed for cleanup
        """
        self.dry_run = dry_run
        self.gandi_api_key = api_key
        self.zone_id = zone_id

        # Gandi's XMLRPC API
        self.client = xmlrpc.client.ServerProxy(api_url)

    @property
    def api_key(self):
        """
        Gandi API key
        """
        return self.gandi_api_key

    @property
    def client_zone(self):
        """
        Client domain zone API endpoint
        """
        return self.client.domain.zone

    def get_dns_record_list(self, zone_id):
        """
        Returns list of all DNS entries for the specified zone
        """
        dns_entries = []
        dns_entry_count = self.client.domain.zone.record.count(self.api_key, self.zone_id, 0)

        for page_num in range(int(dns_entry_count / BATCH_SIZE) + 1):
            dns_entries += self.client.domain.zone.record.list(
                self.api_key,
                self.zone_id,
                0,
                {
                    'items_per_page': BATCH_SIZE,
                    'page': page_num
                }
            )

        return dns_entries

    def delete_dns_record(self, zone_id, zone_version_id, record_name):
        """
        Delete a record from a version of the domain
        """
        # Delete record
        try:
            self.client_zone.record.delete(self.api_key, zone_id, zone_version_id, {
                'type': ['A', 'CNAME'],
                'name': record_name,
            })
        except xmlrpc.client.Fault as e:
            logger.error("  > FAILED Deleting DNS entries for %s...", record_name)
            logger.error("  > ERROR: %s", e)

    def create_new_zone_version(self, zone_id):
        """
        Create a new version of the domain, based on the current version
        Returns the `version_id` of the version
        """
        try:
            return self.client_zone.version.new(self.api_key, zone_id)
        except xmlrpc.client.Fault as e:
            logger.error("FAILED Creating a new DNS zone.")
            logger.error("ERROR: %s", e)
            return None

    def set_zone_version(self, zone_id, zone_version_id):
        """
        Set a version of the domain per id
        """
        try:
            return self.client_zone.version.set(self.api_key, zone_id, zone_version_id)
        except xmlrpc.client.Fault as e:
            logger.error("FAILED updating DNS entries.")
            logger.error("ERROR: %s", e)

    def run_cleanup(self, hashes_to_clean):
        """
        Runs Gandi's DNS cleanup using XMLRPC client using their API

        cleaned_up_hashes: List of hashes deleted on the previous steps of the
        cleanup
        """
        logger.info("\n --- Starting  Gandi DNS Cleanup ---")
        if self.dry_run:
            logger.info("Running in DRY_RUN mode, no actions will be taken.")

        records_to_delete = set()

        # Get DNS records
        dns_records = self.get_dns_record_list(self.zone_id)
        logger.info("Found %s DNS entries...", len(dns_records))

        # Add all records with hashes of recourses that are marked for deletion
        # or have been marked for deletion
        for record in dns_records:
            if any(hash in record['name'] for hash in hashes_to_clean):
                dns_records.remove(record)
                records_to_delete.add(record['name'])

        logger.info(
            "Found %i entries related to old instances.",
            len(records_to_delete)
        )

        if len(records_to_delete):
            logger.info("Starting cleanup...")
            # Create new zone version
            new_zone_version = self.create_new_zone_version(self.zone_id)

            if new_zone_version:
                # Delete entries
                for record in records_to_delete:
                    logger.info("  > DELETING DNS entries for %s...", record)
                    # Delete record
                    self.delete_dns_record(
                        zone_id=self.zone_id,
                        zone_version_id=new_zone_version,
                        record_name=record
                    )

                # Set new zone as current
                if not self.dry_run:
                    self.set_zone_version(
                        zone_id=self.zone_id,
                        zone_version_id=new_zone_version
                    )
