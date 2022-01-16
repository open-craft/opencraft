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
from ruamel import yaml
from django.db import transaction


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

    STATUS_CHOICES = (
        (PENDING, 'Pending',),
        (TRIGGERED, 'Triggered Deployment',),
        (DEPLOYED, 'Deployed',),
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=PENDING)


    def build_trigger_payload(self) -> Dict[str, Any]:
        instance = self.instance.instance
        payload = {
            "variables[INSTANCE_NAME]": instance.name,
            "variables[DEPLOYMENT_REQUEST_ID]": self.pk,
            "variables[NEW_INSTANCE_TRIGGER]": True,

            "TUTOR_LMS_HOST": instance.external_lms_domain if instance.external_lms_domain else instance.internal_lms_domain,
            "TUTOR_PREVIEW_LMS_HOST": instance.external_lms_preview_domain if instance.external_lms_preview_domain else instance.internal_lms_preview_domain,
            "TUTOR_CMS_HOST": instance.external_studio_domain if instance.external_studio_domain else instance.internal_studio_domain,
            "TUTOR_DISCOVERY_HOST": instance.external_discovery_domain if instance.external_discovery_domain else instance.internal_discovery_domain,
            "TUTOR_ECOMMERCE_HOST": instance.external_ecommerce_domain if instance.external_ecommerce_domain else instance.internal_ecommerce_domain,
        }

        payload.update(self.overrides)
        return payload

    def trigger_pipeline(self) -> Optional[Dict[str, Any]]:
        """
        Trigger a deployment pipeline on GitLab.
        """
        if self.status == self.PENDING:
            instance = self.instance.instance
            gitlab_client = instance.repository.gitlab_client
            response = gitlab_client.trigger_pipeline(
                variables=self.build_trigger_payload()
            )
            self.status = self.TRIGGERED
            self.save()
            return response
