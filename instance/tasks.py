# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
Worker tasks for instance hosting & management
"""

# Imports #####################################################################

import logging

from huey.contrib.djhuey import db_task

from instance.models.openedx_instance import OpenEdXInstance


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Tasks #######################################################################

@db_task()
def spawn_appserver(instance_ref_id, mark_active_on_success=False, num_attempts=1):
    """
    Create a new AppServer for an existing instance.

    instance_ref_id should be the ID of an InstanceReference (instance.ref.pk)

    Optionally mark the new AppServer as active when the provisioning completes.
    Optionally retry up to 'num_attempts' times
    """
    for i in range(1, num_attempts + 1):
        logger.info('Retrieving instance: ID=%s', instance_ref_id)
        # Fetch the instance inside the loop, in case it has been updated
        instance = OpenEdXInstance.objects.get(ref_set__pk=instance_ref_id)

        instance.logger.info('Spawning new AppServer, attempt %d of %d', i, num_attempts)
        appserver_id = instance.spawn_appserver()
        if appserver_id:
            if mark_active_on_success:
                # If the AppServer provisioned successfully, make it the active one:
                # Note: if I call spawn_appserver() twice, and the second one provisions sooner, the first one may then
                # finish and replace the second as the active server. We are not really worried about that for now.
                instance.set_appserver_active(appserver_id)
            break
