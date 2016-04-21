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

from instance import github
from instance.models.instance import Instance, SingleVMOpenEdXInstance
from instance.serializers.instance import (
    SingleVMOpenEdXInstanceListSerializer, SingleVMOpenEdXInstanceDetailSerializer
)
from instance.tasks import provision_instance


# Views - API #################################################################

class SingleVMOpenEdXInstanceViewSet(viewsets.ModelViewSet):
    """
    SingleVMOpenEdXInstance API ViewSet
    """
    queryset = SingleVMOpenEdXInstance.objects.all()

    @detail_route(methods=['post'], permission_classes=[IsAuthenticated])
    def provision(self, request, pk=None):
        """
        Start the (re-)provisioning of an instance
        """
        instance = self.get_object()
        if instance.status in (Instance.Status.WaitingForServer, Instance.Status.ConfiguringServer):
            return Response({'status': 'Instance is not ready for reprovisioning'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            instance.set_to_branch_tip()
        except github.ObjectDoesNotExist:
            return Response({
                'status': ("Branch '{0}' not found."
                           'Has it been deleted on GitHub?'.format(instance.branch_name))
            }, status=status.HTTP_400_BAD_REQUEST)

        provision_instance(pk)
        return Response({'status': 'Instance provisioning started'})

    def get_serializer_class(self):
        """
        Return the list serializer for the list action, and the detail serializer otherwise.
        """
        if self.action == 'list':
            return SingleVMOpenEdXInstanceListSerializer
        return SingleVMOpenEdXInstanceDetailSerializer
