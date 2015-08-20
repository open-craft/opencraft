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
Instance views
"""

# Imports #####################################################################

from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from instance.models.instance import OpenEdXInstance
from instance.serializers import OpenEdXInstanceSerializer
from instance.tasks import provision_instance


# Views - API #################################################################

class OpenEdXInstanceViewSet(viewsets.ModelViewSet):
    """
    OpenEdXInstance API ViewSet
    """
    queryset = OpenEdXInstance.objects.all()
    serializer_class = OpenEdXInstanceSerializer

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def provision(self, request, pk=None):
        """
        Start the (re-)provisioning of an instance
        """
        instance = self.get_object()
        if instance.status not in (instance.EMPTY, instance.READY):
            return Response({'status': 'Instance is not ready for reprovisioning'},
                            status=status.HTTP_403_FORBIDDEN)

        instance.set_to_branch_tip()
        provision_instance(pk)

        return Response({'status': 'Instance provisioning started'})
