# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
from instance.gandi import GandiAPI

# Logging #####################################################################

logger = logging.getLogger('integration_cleanup')


# Constants ###################################################################

BATCH_SIZE = 200


# Classes #####################################################################

class DnsCleanupInstance(GandiAPI):
    """
    Handles the cleanup of dangling DNS entries
    """
    def __init__(self, zone_id, api_key, dry_run):
        """
        Set up variables needed for cleanup
        """
        self.dry_run = dry_run
        self.gandi_api_key = api_key
        self.zone_id = zone_id

        super(DnsCleanupInstance, self).__init__()

    @property
    def api_key(self):
        """
        Gandi API key
        """
        return self.gandi_api_key

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
            "Found %i entries related to old instances. Starting deletion process...",
            len(records_to_delete)
        )

        # Create new zone version
        new_zone_version = self.create_new_zone_version(self.zone_id)

        # Delete entries
        for record in records_to_delete:
            logger.info("  > DELETING DNS entries for %s...", record)
            # Delete record
            try:
                self.delete_dns_record(
                    zone_id=self.zone_id,
                    zone_version_id=new_zone_version,
                    record_name=record
                )
            except xmlrpc.client.Fault as e:
                logger.info("  > FAILED Deleting DNS entries for %s...", record)
                logger.info("  > ERROR: %s", e)

        # Set new zone as current
        if not self.dry_run:
            self.set_zone_version(
                zone_id=self.zone_id,
                zone_version_id=new_zone_version
            )
