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

from django.contrib.postgres.fields import JSONField
from django.db import models

from grove.models.gitlabpipeline import GitlabPipeline
from instance.models.deployment import Deployment


class GroveDeployment(Deployment):
    """
    GroveDeployment model tracks GitLab CI pipeline deployments.

    GitLab CI pipeline based deployments are the opposite of OpenStack based
    deployments. The Console Backend is only responsible for triggering the
    pipeline and listening for webhooks.
    """

    overrides = JSONField(null=True, blank=True)

    PENDING = 0
    TRIGGERED = 1
    DEPLOYED = 2
    CANCELLED = 3

    STATUS_CHOICES = (
        (PENDING, 'Pending',),
        (TRIGGERED, 'Triggered Deployment',),
        (DEPLOYED, 'Deployed',),
        (CANCELLED, 'Cancelled'),
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=PENDING)
    pipeline = models.ForeignKey(GitlabPipeline, on_delete=models.SET_NULL, null=True, blank=True)


    def build_trigger_payload(self) -> Dict[str, Any]:
        """
        Assemble the payload for the GitLab pipeline to trigger a new deployment.
        """
        instance = self.instance.instance
        payload = {
            "variables[INSTANCE_NAME]": instance.name,
            "variables[DEPLOYMENT_REQUEST_ID]": self.pk,
            "variables[NEW_INSTANCE_TRIGGER]": True,

            "TUTOR_LMS_HOST": instance.external_lms_domain or instance.internal_lms_domain,
            "TUTOR_PREVIEW_LMS_HOST": instance.external_lms_preview_domain or instance.internal_lms_preview_domain,
            "TUTOR_CMS_HOST": instance.external_studio_domain or instance.internal_studio_domain,
            "TUTOR_DISCOVERY_HOST": instance.external_discovery_domain or instance.internal_discovery_domain,
            "TUTOR_ECOMMERCE_HOST": instance.external_ecommerce_domain or instance.internal_ecommerce_domain,
        }

        payload.update(self.overrides)
        return payload

    def build_abort_pipeline_trigger_payload(self, pipeline_id) -> Dict[str, Any]:
        """
        Assemble the deployment pipeline cancellation payload.
        """
        return {
            "variables[ABORT_DEPLOYMENT_TRIGGER]": True,
            "variables[PIPELINE_ID]": pipeline_id,
        }

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
