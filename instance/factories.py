# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
Instance app - Factory functions for creating instances
"""

# Imports #####################################################################

import logging
import re
import yaml

from django.conf import settings

from grove.models.instance import GroveInstance
from grove.models.repository import get_default_repository
from grove.switchboard import SWITCH_GROVE_DEPLOYMENTS, is_feature_enabled
from instance import ansible
from instance.models.database_server import MySQLServer, MongoDBServer
from instance.models.mixins.storage import StorageContainer
from instance.models.openedx_instance import OpenEdXInstance
from grove.models.repository import get_default_repository


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Functions ###################################################################

def _check_environment():
    """
    Check environment and report potential problems for production instances
    """
    grove_repo = get_default_repository()
    if not grove_repo:
        logger.warning("Default Grove repository is not available!")
        return False
    return True


def is_valid_domain_name(sub_domain):
    """
    Validate subdomain names passed to instance factory functions,
    using the same regex as the BetaTestApplication.subdomain field validator.
    """

    regex = r'^[a-z0-9]([a-z0-9\-]+[a-z0-9])?$'

    return re.match(regex, sub_domain)


def instance_factory(**kwargs):
    """
    Factory function for creating instances.

    Returns a newly created OpenEdXInstance.

    Callers can use keyword arguments to pass in non-default values
    for any field that is defined on the OpenEdXInstance model.

    The only mandatory argument is `sub_domain`.

    When called without any additional arguments, the instance that is returned
    will have its fields set to default values that are appropriate
    for *sandbox* instances.

    To create an instance with default settings that are suitable for production,
    use `production_instance_factory`.
    """
    # Ensure caller provided required arguments
    assert "sub_domain" in kwargs

    # Prevent multiple instances whose domains are identical except for the letter casing
    kwargs["sub_domain"] = kwargs["sub_domain"].lower()

    # Create instance
    instance = OpenEdXInstance.objects.create(**kwargs)
    return instance


def production_instance_factory(**kwargs) -> GroveInstance:
    """
    Factory function for creating production instances.

    Returns a newly created OpenEdXInstance.

    Callers can use keyword arguments to pass in non-default values
    for any field that is defined on the OpenEdXInstance model.

    The only mandatory argument is `sub_domain`.

    When called without any additional arguments, the instance that is returned
    will have its fields set to default values that are appropriate
    for *production* instances.

    To create an instance with default settings that are suitable for sandboxes,
    use `instance_factory`.
    """
    # NOTE: The long-term goal is to eliminate differences between sandboxes
    # and production instances, and for this function to disappear.
    # Please do not add behavior that is specific to production instances here.

    # Ensure caller provided required arguments
    assert "sub_domain" in kwargs
    assert is_valid_domain_name(kwargs.get('sub_domain'))

    # Check environment and report potential problems
    environment_ready = _check_environment()

    if not environment_ready:
        logger.warning("Environment not ready. Please fix the problems above, then try again. Aborting.")
        return None

    configuration_extra_settings = kwargs.pop("configuration_extra_settings", "")
    if configuration_extra_settings:
        configuration_extra_settings = yaml.load(configuration_extra_settings, Loader=yaml.SafeLoader)
    else:
        configuration_extra_settings = {}
    extra_settings = yaml.dump(
        ansible.dict_merge(
            settings.PRODUCTION_INSTANCE_EXTRA_CONFIGURATION,
            configuration_extra_settings
        ),
        default_flow_style=False
    )
    instance_kwargs = dict(
        edx_platform_repository_url=settings.STABLE_EDX_PLATFORM_REPO_URL,
        edx_platform_commit=settings.STABLE_EDX_PLATFORM_COMMIT,
        configuration_source_repo_url=settings.STABLE_CONFIGURATION_REPO_URL,
        configuration_version=settings.STABLE_CONFIGURATION_VERSION,
        openedx_release=settings.OPENEDX_RELEASE_STABLE_REF,
        configuration_extra_settings=extra_settings,
    )

    repository = get_default_repository()
    project_id = repository.project_id
    instance_id = repository.unleash_instance_id
    instance_kwargs.update(kwargs)

    if is_feature_enabled(repository.gitlab_client.base_url, project_id, instance_id, SWITCH_GROVE_DEPLOYMENTS):
        instance_kwargs.update({"repository": repository})

        # Create Grove instance
        return GroveInstance.objects.create(**instance_kwargs)

    production_instance = GroveInstance.objects.create(**instance_kwargs)
    return production_instance
