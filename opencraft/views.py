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
OpenCraft views
"""

# Imports #####################################################################

from django.views.generic.base import RedirectView
from django.urls import reverse
from django.conf import settings
from registration.models import BetaTestApplication
from instance.models.instance import InstanceReference

# Views #######################################################################


class IndexView(RedirectView):
    """
    Index view
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Redirect instance manager users to the instance list, and anyone else to the registration form
        """
        user = self.request.user
        try:
            beta_test_user = BetaTestApplication.objects.filter(user=user)
        except TypeError:
            beta_test_user = []
        if InstanceReference.can_manage(user):
            return reverse('instance:index')
        elif beta_test_user:
            return settings.USER_CONSOLE_FRONTEND_URL
        else:
            return reverse('login')
