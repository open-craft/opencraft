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
The Gitlab pipeline model.
"""

from django_extensions.db.models import TimeStampedModel

from django.db import models

from instance.models.instance import InstanceReference
from instance.models.openedx_deployment import DeploymentState


class GitlabPipeline(TimeStampedModel):
    """
    GitlabPipeline model tracks the pipeline status for deployments.
    """
    CREATED = 0
    RUNNING = 1
    SUCCESS = 2
    FAILED = 3
    SKIPPED = 4
    CANCELLED = 5

    STATUS_NAMES = (
        'created',
        'running',
        'success',
        'failed',
        'skipped',
        'cancelled',
    )

    STATUS_CHOICES = (
        (CREATED, STATUS_NAMES[CREATED]),
        (RUNNING, STATUS_NAMES[RUNNING]),
        (SUCCESS, STATUS_NAMES[SUCCESS]),
        (FAILED, STATUS_NAMES[FAILED]),
        (SKIPPED, STATUS_NAMES[SKIPPED]),
        (CANCELLED, STATUS_NAMES[CANCELLED]),
    )

    pipeline_id = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text="Gitlab Pipeline ID"
    )
    instance = models.ForeignKey(InstanceReference, on_delete=models.CASCADE)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=CREATED)

    def update_status(self, new_status=None):
        """
        Update pipeline status if new status is known.
        """
        updated_status = 0
        for k, v in self.STATUS_CHOICES:
            if new_status == v:
                updated_status = k

        if self.status != updated_status:
            self.status = updated_status
            self.save()

        if self.status == self.FAILED:
            deployment = self.grovedeployment_set.last()
            deployment.status = deployment.FAILED
            deployment.save()

    def get_deployment_status(self):
        """
        Retrieve the deployment status.
        """
        if self.status == self.SUCCESS:
            self.instance.instance.successfully_provisioned = True
            self.instance.instance.save()
            return DeploymentState.healthy
        elif self.status in [self.CREATED, self.RUNNING]:
            return DeploymentState.provisioning
        elif self.status in [self.FAILED, self.SKIPPED, self.CANCELLED]:
            return DeploymentState.unhealthy

        return DeploymentState.offline
