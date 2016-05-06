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
    if settings.INSTANCE_MYSQL_URL is None:
        logger.warning("URL for external MySQL database is missing. Adjust INSTANCE_MYSQL_URL setting.")
    if settings.INSTANCE_MONGO_URL is None:
        logger.warning("URL for external Mongo database is missing. Adjust INSTANCE_MONGO_URL setting.")


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

    # Create instance
    instance = OpenEdXInstance.objects.create(**kwargs)
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
    _check_environment()

    # Create instance
    production_instance = OpenEdXInstance(**kwargs)
    if "use_ephemeral_databases" not in kwargs:
        production_instance.use_ephemeral_databases = False
    if "configuration_version" not in kwargs:
        production_instance.configuration_version = settings.LATEST_OPENEDX_RELEASE
    if "openedx_release" not in kwargs:
        production_instance.openedx_release = settings.LATEST_OPENEDX_RELEASE
    if "configuration_extra_settings" not in kwargs:
        template = loader.get_template('instance/ansible/prod-vars.yml')
        production_instance.configuration_extra_settings = template.render({})
    production_instance.save()
    return production_instance
