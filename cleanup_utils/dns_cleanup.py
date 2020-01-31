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

from instance.gandi import GandiV5API

# Logging #####################################################################

logger = logging.getLogger('integration_cleanup')


# Constants ###################################################################

BATCH_SIZE = 200


# Classes #####################################################################


class DNSCleanupInstance:
    """
    Clean up the DNS records.
    """
    def __init__(self, api_key, base_domain, dry_run=False):
        self.client = GandiV5API(api_key=api_key)
        self.base_domain = base_domain
        self.dry_run = dry_run

    def run_cleanup(self, hashes_to_clean):
        """
        Cleans up the DNS records using the Gandi API.
        """

        logger.info('\n --- Starting Gandi DNS cleanup ---')
        if self.dry_run:
            logger.info('Running in DRY_RUN mode, no actions will be taken.')

        logger.info('Deleting the following DNS records:')
        for hash_ in hashes_to_clean:
            record = hash_ + self.base_domain if not hash_.endswith(self.base_domain) else hash_
            logger.info('  %s', record)

            if not self.dry_run:
                self.client.remove_dns_record(record, type='CNAME')
