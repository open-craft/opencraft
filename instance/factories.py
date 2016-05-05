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

from django.conf import settings
from django.template import loader

from instance.models.openedx_instance import OpenEdXInstance


# Functions ###################################################################

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
    assert "sub_domain" in kwargs
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
    assert "sub_domain" in kwargs
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
