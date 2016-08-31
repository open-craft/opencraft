# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
Helper function to upgrade production instances from Dogwood to Eucalyptus.
"""

import logging

from instance.models.openedx_instance import OpenEdXInstance
from instance.tasks import spawn_appserver

logger = logging.getLogger(__name__)


def get_instances_to_upgrade():
    """Select instances that need to be upgraded to Eucalyptus."""
    return OpenEdXInstance.objects.filter(           # Select instances
        active_appserver___status="running",         # that are running
        openedx_release__contains="dogwood",         # on dogwood
        use_ephemeral_databases=False,               # and use persistent databases.
    )


def upgrade_to_eucalyptus(instances):
    """Upgrade all OpenEdXInstances in the given iterable to Eucalyptus."""
    for instance in instances:
        instance.refresh_from_db()
        logger.info("Upgrading instance %s to Eucalyptus...", instance)
        instance.configuration_extra_settings += "\nCOMMON_EUCALYPTUS_UPGRADE: true\n"
        instance.edx_platform_repository_url = "https://github.com/open-craft/edx-platform"
        instance.edx_platform_commit = "opencraft-release/eucalyptus.1"
        instance.configuration_source_repo_url = "https://github.com/open-craft/configuration"
        instance.configuration_version = "opencraft-release/eucalyptus.1"
        instance.openedx_release = "open-release/eucalyptus.1"
        instance.save()
        for appserver in instance.appserver_set.iterator():
            appserver.terminate_vm()
        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=1)


def clean_up_after_upgrade(instances):
    """Remove Eucalyptus upgrade flag from the instance configuration."""
    for instance in instances:
        instance.refresh_from_db()
        instance.configuration_extra_settings = instance.configuration_extra_settings.replace(
            "\nCOMMON_EUCALYPTUS_UPGRADE: true\n", ""
        )
        instance.save()
