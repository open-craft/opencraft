# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Instance views - decorators
"""

# Imports #####################################################################

from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test

from instance.models.instance import InstanceReference


# Decorators ##################################################################

def instance_manager_required(function=None, redirect_to=None, raise_exception=False):
    """
    View decorator that checks whether the user is an InstanceManager, i.e.
      has the permission to browse their own instances or all instances.

    Modeled on django.contrib.auth.decorators.permission_required().

    :param function: view function to wrap
    :param redirect_to: URL to redirect to if user is not an InstanceManager user
    :param raise_exception: if set, will raise PermissionDenied if user is not an InstanceManager user.
    """
    def check_perm(user):
        """Checks if the user is an instance manager"""
        if InstanceReference.can_manage(user):
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            raise PermissionDenied
        # Or, show login form.
        return False

    # Use the user_passes_test view decorator to handle redirect.
    actual_decorator = user_passes_test(
        check_perm,
        login_url=redirect_to,
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
