# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <contact@opencraft.com>
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
Background tasks for by the Grove app.
"""
import logging
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from grove.models.deployment import GroveDeployment
from instance.models.deployment import DeploymentType

logger = logging.getLogger(__name__)


@db_periodic_task(crontab(minute='*'))
def trigger_grove_deployment():
    """
    Triggers Grove for deployment.

    There are some restrictions in Grove at the moment.
        - for new instance deployment we can't run deployments in parallel
        - for existing instances we can run deployments in parallel

    This task will periodicly check and trigger deployment when it can.
    """
    pending_deployments = GroveDeployment.objects.filter(status=GroveDeployment.PENDING).order_by('modified')

    logger.info('There are %s pending deployments!', len(pending_deployments))

    for deployment in pending_deployments:

        if deployment.type == DeploymentType.registration.name and deployment.instance.instance.repository.gitlab_client.is_there_any_pipeline_running():
            # this is a new deployment via registration and there is other
            # pipelines running, so we can't deploy now. We could use `continue`
            # here, but that might create a long delay before starting deployments.
            #
            # so, instead we will not trigger any deployments and wait for existing
            # one's to finish, so that we can deploy this new instance.
            break

        logger.info('Triggering deployment for %s!', len(deployment.instance.name))
        deployment.trigger_pipeline()
