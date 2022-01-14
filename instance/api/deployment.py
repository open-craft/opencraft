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
DeploymentType API
"""
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import viewsets

from instance.api.permissions import IsSuperUser
from instance.models.deployment import DeploymentType
from instance.serializers.deployment import DeploymentTypeSerializer


class DeploymentTypeViewSet(viewsets.ViewSet):
    """
    API to list all *unique* InstanceTag instances.
    """
    serializer_class = DeploymentTypeSerializer
    permission_classes = [IsSuperUser]

    def list(self, request):
        """
        List API for all deployment types.
        """
        deployments = sorted(DeploymentType, key=lambda d: d.value)
        serializer = self.serializer_class(deployments, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        """
        Retrieve API for a DeploymentType.

        pk: Name of DeploymentType item.
        """
        try:
            item = DeploymentType[pk]
        except KeyError:
            raise NotFound
        serializer = self.serializer_class(item)
        return Response(serializer.data)
