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
GitLab client used by Grove.
"""

from urllib.parse import urljoin
from typing import Any, Dict, List, Optional

import requests
from django.core.exceptions import ImproperlyConfigured

GitLabToken: Optional[str] = None

PIPELINE_RUNNING_STATUSES: List[str] = [
    'created',
    'waiting_for_resource',
    'preparing',
    'pending',
    'running'
]


class GitLabClient:
    """
    A client to call basic operations on GitLab.
    """

    def __init__(
            self,
            base_url: str,
            project_id: int,
            ref: str,
            username: str,
            personal_access_token: str,
            trigger_token: str,
    ):
        self.base_url = base_url
        self.username = username
        self.personal_access_token = personal_access_token
        self.trigger_token = trigger_token
        self.project_id = project_id
        self.ref = ref

    def trigger_pipeline(self, variables: Dict[str, Any]) -> dict:
        """
        Trigger a pipeline on GitLab using the given token if set.

        If the trigger returned with a not OK status code, an exception is raised, otherwise, the
        response data is returned.
        """

        if self.trigger_token is None:
            raise ImproperlyConfigured("GitLab token is not set.")

        response = requests.post(
            urljoin(self.base_url, f"projects/{self.project_id}/trigger/pipeline"),
            json={
                **variables,
                "ref": self.ref,
                "token": self.trigger_token,
            }
        )

        response.raise_for_status()
        return response.json()

    def is_there_any_pipeline_running(self):
        """
        Checks if there is any pipeline running for current GitLab project and branch (ref).

        Returns:
            bool - False if there is no pipeline running, True otherwise.
        """

        response = requests.get(
            urljoin(self.base_url, f"projects/{self.project_id}/pipelines"),
            params={
                'ref': self.ref
            },
            headers={
                'PRIVATE-TOKEN': self.personal_access_token,
            },
        )
        response.raise_for_status()
        pipelines: List[dict] = response.json()

        # any pipeline that has status any of created, waiting_for_resource, preparing, pending
        # or running will be considered as running pipeline.
        return any([pipeline['status'] in PIPELINE_RUNNING_STATUSES for pipeline in pipelines])
