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
This management command will migrate instances using ephemeral databases
to external databases instead.

This is a prerequisite to deprecate ephemeral databases, cf. #327
"""

import logging

from django.core.management.base import BaseCommand

from instance.models.instance import InstanceReference
from instance.tasks import spawn_appserver

LOG = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    This management command will migrate instances using ephemeral databases
    to external databases instead.
    """
    help = (
        'Disables ephemeral databases for all instances that are currently using them '
        'and provisions new app servers pointing to persistent databases.'
    )

    def handle(self, *args, **options):
        """
        Disable ephemeral databases for all instances that are currently using them
        and provision new app servers pointing to persistent databases.
        """

        # Identify instances that need updating
        refs = {
            ref for ref in
            InstanceReference.objects.filter(is_archived=False) if ref.instance.use_ephemeral_databases
        }
        LOG.info('Found "%d" instances using ephemeral databases', len(refs))

        for ref in refs:
            # Disable ephemeral support and spawn a new AppServer
            LOG.info('Migrating %s to use persistent databases', ref.instance.name)
            ref.instance.use_ephemeral_databases = False
            ref.instance.save()
            spawn_appserver(
                instance_ref_id=ref.id,
                mark_active_on_success=True,
                deactivate_old_appservers=True,
                num_attempts=3)
            LOG.info('Migrated and started provisioning a new app server for %s', ref.instance.name)
