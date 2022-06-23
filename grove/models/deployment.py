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
The Grove deployment model.
"""

from typing import Dict, Any, Optional

from django.db import models

from grove.models.gitlabpipeline import GitlabPipeline
from grove.models.mixins.payload import PayloadMixin
from instance.models.deployment import Deployment
from instance.utils import publish_data


class GroveDeployment(Deployment, PayloadMixin):
    """
    GroveDeployment model tracks GitLab CI pipeline deployments.

    GitLab CI pipeline based deployments are the opposite of OpenStack based
    deployments. The Console Backend is only responsible for triggering the
    pipeline and listening for webhooks.
    """

    PENDING = 0
    TRIGGERED = 1
    DEPLOYED = 2
    CANCELLED = 3
    FAILED = 4

    STATUS_NAMES = (
        "Pending",
        "Triggered Deployment",
        "Deployed",
        "Cancelled",
        "Failed",
    )

    STATUS_CHOICES = (
        (PENDING, STATUS_NAMES[PENDING],),
        (TRIGGERED, STATUS_NAMES[TRIGGERED],),
        (DEPLOYED, STATUS_NAMES[DEPLOYED],),
        (CANCELLED, STATUS_NAMES[CANCELLED]),
        (FAILED, STATUS_NAMES[FAILED]),
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=PENDING)
    pipeline = models.ForeignKey(GitlabPipeline, on_delete=models.SET_NULL, null=True, blank=True)

    def trigger_pipeline(self) -> Optional[Dict[str, Any]]:
        """
        Trigger a deployment pipeline on GitLab.
        """
        if self.status != self.PENDING:
            return None

        instance = self.instance.instance
        gitlab_client = instance.repository.gitlab_client
        response = gitlab_client.trigger_pipeline(
            variables=self.build_trigger_payload()
        )
        self.status = self.TRIGGERED
        self.save()
        return response

    def check_status(self) -> Optional[Dict[str, Any]]:
        """
        Check gitlab pipeline status
        """
        return self.pipeline.get_deployment_status()

    def cancel_deployment(self) -> Optional[Dict[str, Any]]:
        """
        Cancel ongoing deployment pipeline on Gitlab
        """
        instance = self.instance.instance
        gitlab_client = instance.repository.gitlab_client
        pipeline_id = self.pipeline.pipeline_id
        response = gitlab_client.trigger_pipeline(
            variables=self.build_abort_pipeline_trigger_payload(pipeline_id)
        )
        self.status = self.CANCELLED
        self.save()
        return response

    def save(self, **kwargs):
        super(GroveDeployment, self).save(**kwargs)

        publish_data({
            'type': 'grove_deployment_update',
            'deployment_id': self.id,
            'instance_id': self.instance.id,
        })
