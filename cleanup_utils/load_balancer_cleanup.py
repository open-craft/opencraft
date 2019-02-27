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
Load balancer clean up script
Removes all the stale load balancer configuration fragments
"""

import logging
import os
import pathlib

from instance import ansible

# Logging #####################################################################

logger = logging.getLogger('integration_cleanup')

# Classes #####################################################################


class LoadBalancerCleanup:
    """
    Searches and removes all the stale load balancer configuration fragments.
    """
    def __init__(self, load_balancer_address, fragment_prefix, age_limit, dry_run):
        """Sets up the variables needed for the cleanup"""
        self.load_balancer_address = load_balancer_address
        self.fragment_prefix = fragment_prefix
        self.age_limit = age_limit
        self.dry_run = dry_run

    def run_cleanup(self):
        """Run the actual cleanup"""
        logger.info("\n --- Starting Load balancer fragments cleanup ---")

        if self.dry_run:
            logger.info("Running in DRY_RUN mode, no actions will be taken")

        playbook_path = pathlib.Path(
            os.path.abspath(os.path.dirname(__file__))
        ) / "playbooks/load_balancer_cleanup.yml"

        ansible_vars = (
            "DAYS_OLDER_THAN: {age_limit}\n"
            "FRAGMENT_PATTERN: {fragment_prefix}*\n"
            "REMOVE_FRAGMENTS: {remove_fragments}\n"
        ).format(
            age_limit=self.age_limit,
            fragment_prefix=self.fragment_prefix,
            remove_fragments='true' if self.dry_run else 'false'
        )

        return_code = ansible.capture_playbook_output(
            requirements_path=str(playbook_path.parent / "requirements.txt"),
            playbook_path=str(playbook_path),
            inventory_str=self.load_balancer_address,
            vars_str=ansible_vars,
            username='ubuntu',
            logger_=logger,
        )
        if return_code != 0:
            raise Exception("Playbook to remove stale load balancer fragments failed")
