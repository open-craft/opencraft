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
MySQL Cleanup Script

Cleans up all MySQL databases left behind from CI
"""

import logging


# Logging ####################################################################

logger = logging.getLogger('integration_cleanup')


# Classes ####################################################################

class MySqlCleanupInstance:
    """
    Handles the cleanup of old MySQL databases
    """
    def __init__(self, age_limit, url, dry_run):
        """
        Set up variables needed for cleanup
        """
        self.age_limit = age_limit
        self.dry_run = dry_run
        self.url = url

    def run_cleanup(self):
        """
        Runs the cleanup of MySQL databases older than the age limit
        """
        logger.info("\n --- Starting MySQL Cleanup ---")
        if self.dry_run:
            logger.info("Running in DRY_RUN mode, no actions will be taken.")
