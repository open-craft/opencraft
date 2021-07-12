# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2019 OpenCraft <contact@opencraft.com>
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
Worker tasks for periodically building new open edx appservers at intervals.
"""

# Imports #####################################################################

import logging
import datetime

from huey.api import crontab
from huey.contrib.djhuey import db_periodic_task, lock_task

from instance.models.deployment import DeploymentType
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.appserver import Status
from instance.utils import create_new_deployment

# Logging #####################################################################

logger = logging.getLogger(__name__)


# Tasks #######################################################################


@db_periodic_task(crontab(minute="34", hour="*/2"))
@lock_task('launch_periodic_builds-lock')
def launch_periodic_builds():
    """
    Automatically deploy new servers for all Open edX instances configured for periodic builds.
    """
    instances = OpenEdXInstance.objects.filter(
        periodic_builds_enabled=True,
        ref_set__is_archived=False,
    )

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    for instance in instances:
        appservers = instance.appserver_set.order_by("-created").all()
        # NOTE: 'created' is the time when the appserver was created, which is
        # before provisioning begins.
        # if the instance has no appservers or latest appserver is past the
        # interval time, then we spawn a new appserver
        if not appservers or (now - appservers[0].created) >= instance.periodic_builds_interval:

            # check for appservers in-progress; if so, we don't want to launch
            # a new one on top
            for appserver in appservers:
                if appserver.status in (
                        Status.New,
                        Status.WaitingForServer,
                        Status.ConfiguringServer,
                ):
                    break
            else:
                # NOTE: this is async - enqueues as a new huey task and returns immediately
                create_new_deployment(
                    instance,
                    num_attempts=instance.periodic_builds_retries + 1,
                    mark_active_on_success=True,
                    deployment_type=DeploymentType.periodic,
                )
