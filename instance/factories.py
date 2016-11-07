# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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

from django.conf import settings
from django.template import loader

from instance import ansible
from instance.models.database_server import MySQLServer, MongoDBServer
from instance.models.openedx_instance import OpenEdXInstance


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Functions ###################################################################

def _check_environment():
    """
    Check environment and report potential problems for production instances
    """
    if not settings.SWIFT_ENABLE:
        logger.warning("Swift support is currently disabled. Adjust SWIFT_ENABLE setting.")
        return
    if not MySQLServer.objects.exists() and settings.DEFAULT_INSTANCE_MYSQL_URL is None:  # pylint: disable=no-member
        logger.warning(
            "No MySQL servers configured, and default URL for external MySQL database is missing."
            "Create at least one MySQLServer, or set DEFAULT_INSTANCE_MYSQL_URL in your .env."
        )
        return
    if not MongoDBServer.objects.exists() and settings.DEFAULT_INSTANCE_MONGO_URL is None:  # pylint: disable=no-member
        logger.warning(
            "No MongoDB servers configured, and default URL for external MongoDB database is missing."
            "Create at least one MongoDBServer, or set DEFAULT_INSTANCE_MONGO_URL in your .env."
        )
        return
    return True


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

    # Ensure instance uses ephemeral databases by default,
    # irrespective of current value of INSTANCE_EPHEMERAL_DATABASES setting
    instance_kwargs = dict(use_ephemeral_databases=True)
    instance_kwargs.update(kwargs)

    # Create instance
    instance = OpenEdXInstance.objects.create(**instance_kwargs)
    return instance


def production_instance_factory(**kwargs):
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

    # Check environment and report potential problems
    environment_ready = _check_environment()

    if not environment_ready:
        logger.warning("Environment not ready. Please fix the problems above, then try again. Aborting.")
        return

    # Gather settings
    production_settings = loader.get_template('instance/ansible/prod-vars.yml').render({})
    configuration_extra_settings = kwargs.pop("configuration_extra_settings", "")
    extra_settings = ansible.yaml_merge(production_settings, configuration_extra_settings)
    instance_kwargs = dict(
        use_ephemeral_databases=False,
        edx_platform_repository_url=settings.STABLE_EDX_PLATFORM_REPO_URL,
        edx_platform_commit=settings.STABLE_EDX_PLATFORM_COMMIT,
        configuration_source_repo_url=settings.STABLE_CONFIGURATION_REPO_URL,
        configuration_version=settings.STABLE_CONFIGURATION_VERSION,
        openedx_release=settings.OPENEDX_RELEASE_STABLE_REF,
        configuration_extra_settings=extra_settings,
    )
    instance_kwargs.update(kwargs)

    # Create instance
    production_instance = OpenEdXInstance.objects.create(**instance_kwargs)
    return production_instance
