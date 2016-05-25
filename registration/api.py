# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
Registration api views
"""

# Imports #####################################################################

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from registration.forms import BetaTestApplicationForm
from registration.views import BetaTestApplicationMixin


# Views #######################################################################

class BetaTestApplicationViewSet(BetaTestApplicationMixin, ViewSet):
    """
    ViewSet for ajax validation of the beta test registration form.
    """
    permission_classes = (AllowAny,)

    def list(self, request):
        """
        Validate the given form input, and return any errors as json.

        Not really a list view, but we have to use `list` to fit into ViewSet
        semantics so this can be part of the browsable api.
        """
        form = BetaTestApplicationForm(request.query_params,
                                       instance=self.get_object())
        return Response(form.errors)
