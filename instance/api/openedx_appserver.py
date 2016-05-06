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
Open edX AppServer API
"""

# Imports #####################################################################

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status, serializers
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from instance.models.instance import InstanceReference
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance
from instance.serializers.appserver import AppServerBasicSerializer
from instance.serializers.openedx_appserver import OpenEdXAppServerSerializer, SpawnAppServerSerializer
from instance.tasks import provision_instance


# Views - API #################################################################


class OpenEdXAppServerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to list and manipulate Open edX AppServers.
    """
    queryset = OpenEdXAppServer.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Return the basic serializer for the list action, and the detailed serializer otherwise.
        """
        if self.action == 'list':
            return AppServerBasicSerializer
        elif self.action == 'create':
            return SpawnAppServerSerializer
        return OpenEdXAppServerSerializer

    def create(self, request):  # pylint: disable=no-self-use
        """
        Spawn a new AppServer for an existing OpenEdXInstance

        Must pass a parameter called 'instance_id' which is the ID of the InstanceReference of
        the OpenEdXInstance that this AppServer is for.
        """
        serializer = SpawnAppServerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance_id = serializer.validated_data['instance_id']

        try:
            instance_ref = InstanceReference.objects.get(pk=instance_id)
        except ObjectDoesNotExist:
            raise NotFound('InstanceReference with ID {} not found.'.format(instance_id))

        instance = instance_ref.instance
        if not isinstance(instance, OpenEdXInstance):
            raise serializers.ValidationError('Invalid InstanceReference ID: Not an OpenEdXInstance.')

        provision_instance(instance_id)
        return Response({'status': 'Instance provisioning started'})

    def get_view_name(self):
        """
        Get the verbose name for each view
        """
        suffix = self.suffix
        if self.action == 'retrieve':
            suffix = "Details"
        return "Open edX App Server {}".format(suffix)
