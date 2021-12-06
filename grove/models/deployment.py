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

from typing import Dict, Any

from django.contrib.postgres.fields import JSONField
from ruamel import yaml

from grove.gitlab import gitlab_client
from instance.models.deployment import Deployment


class GroveDeployment(Deployment):
    """
    GroveDeployment model tracks GitLab CI pipeline deployments.

    GitLab CI pipeline based deployments are the opposite of OpenStack based
    deployments. The Console Backend is only responsible for triggering the
    pipeline and listening for webhooks.
    """

    overrides = JSONField(null=True, blank=True)

    def trigger_pipeline(self) -> Dict[str, Any]:
        """
        Trigger a deployment pipeline on GitLab.
        """

        instance = self.instance.instance
        repository = instance.repository

        return gitlab_client.trigger_pipeline(
            ref=repository.git_ref,
            project_id=repository.project_id,
            token=repository.trigger_token,
            variables={
                "variables[INSTANCE_NAME]": instance.name,
                "variables[DEPLOYMENT_REQUEST_ID]": self.pk,
                "variables[CONFIG_OVERRIDES]": yaml.dump(self.overrides)
            }
        )
