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
Status API
"""
from rest_framework.response import Response
from rest_framework import viewsets

from instance.api.permissions import IsSuperUser
from instance.models.appserver import Status
from instance.serializers.appserver import StatusSerializer


class StatusViewSet(viewsets.ViewSet):
    """
    API to list all AppServer Statuses.
    """
    serializer_class = StatusSerializer
    permission_classes = [IsSuperUser]

    def list(self, request):
        """
        List API for all AppServer Statuses.
        """
        states = sorted(Status.states, key=lambda i: i.name)
        serializer = self.serializer_class(states, many=True)
        return Response(serializer.data)
