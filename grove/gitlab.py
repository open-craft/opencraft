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
from typing import Any, Dict, Optional

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

GitLabToken: Optional[str] = None


class GitLabClient:
    """
    A client to call basic operations on GitLab.
    """

    def __init__(self, base_url: str, token: GitLabToken):
        self.base_url = base_url
        self.token = "" if token is None else token

    def trigger_pipeline(self, ref: str, project_id: int, token: GitLabToken, variables: Dict[str, Any]) -> dict:
        """
        Trigger a pipeline on GitLab using the given token if set.

        If the trigger returned with a not OK status code, an exception is raised, otherwise, the
        response data is returned.
        """

        if token is None and self.token is None:
            raise ImproperlyConfigured("GitLab token is not set.")

        response = requests.post(
            urljoin(self.base_url, f"projects/{project_id}/trigger/pipeline"),
            data={
                "ref": ref,
                "token": token,
                **variables,
            }
        )

        response.raise_for_status()
        return response.json()


gitlab_client = GitLabClient(
    base_url=settings.GITLAB_API_BASE_URL,
    token=settings.GITLAB_API_TOKEN,
)
