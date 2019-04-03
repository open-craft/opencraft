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
Authentication backends
"""

# Imports #####################################################################

from django.contrib.auth import get_user_model
from django.contrib.auth import backends
from django.db.models import Q


# Auth backends ###############################################################

class ModelBackend(backends.ModelBackend):
    """
    Extends the default ModelBackend to fetch users by email address as well as
    by username.
    """
    def authenticate(self, username=None, password=None):
        """
        This is mostly copied from the default ModelBackend. Attempts to fetch
        users by username or email address, instead of just by username.
        """
        if not username or not password:
            return None
        UserModel = get_user_model()  # noqa
        try:
            user = UserModel._default_manager.get(Q(username=username) |
                                                  Q(email=username))
        except (UserModel.DoesNotExist, UserModel.MultipleObjectsReturned):
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password):
                return user
