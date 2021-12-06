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
Registry for feature toggles used by the Console Backend (Ocim).
"""

from urllib.parse import urljoin

from django.conf import settings
from UnleashClient import UnleashClient

SWITCH_GROVE_DEPLOYMENTS: str = "enable_grove_deployments"

# In-memory "cache" for the initialized clients
__clients__ = dict()


def get_unleash_client(url: str, project_id: int, instance_id: str, app_name: str) -> UnleashClient:
    cache_key = f"{project_id}-{instance_id}-{app_name}"

    initialized_client = __clients__.get(cache_key, None)
    if initialized_client is not None:
        return initialized_client

    client = UnleashClient(
        url=url,
        instance_id=instance_id,
        app_name=app_name,
    )

    client.initialize_client()

    __clients__[cache_key] = client
    return client


def is_feature_enabled(base_url: str, project_id: int, instance_id: str, feature: str, **kwargs) -> bool:
    """
    Get the status of the given feature switch in the current environment.

    The results are intentionally not cached.
    """

    client = get_unleash_client(
        url=urljoin(base_url, f"feature_flags/unleash/{project_id}"),
        project_id=project_id,
        instance_id=instance_id,
        app_name=settings.GROVE_ENVIRONMENT,
    )

    return client.is_enabled(feature, **kwargs)
