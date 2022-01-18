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
Open edX AppServer API
"""

# Imports #####################################################################

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from instance.api.permissions import IsSuperUser
from instance.models.instance import InstanceReference
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance
from instance.serializers.appserver import AppServerBasicSerializer
from instance.serializers.openedx_appserver import (
    OpenEdXAppServerLogSerializer,
    OpenEdXAppServerSerializer,
    SpawnAppServerSerializer,
    OpenEdXReleaseSerializer
)
from instance.tasks import make_appserver_active, terminate_appserver
from instance.utils import create_new_deployment
from .filters import IsOrganizationOwnerFilterBackendAppServer, IsOrganizationOwnerFilterBackendInstance
from ..models.deployment import DeploymentType


# Views - API #################################################################


class OpenEdXAppServerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to list and manipulate Open edX AppServers.
    """
    queryset = OpenEdXAppServer.objects.all()
    filter_backends = (IsOrganizationOwnerFilterBackendAppServer,)

    def get_serializer_class(self):
        """
        Return the basic serializer for the list action, and the detailed serializer otherwise.
        """
        if self.action == 'list':
            return AppServerBasicSerializer
        if self.action == 'create':
            return SpawnAppServerSerializer
        return OpenEdXAppServerSerializer

    def create(self, request):
        """
        Spawn a new AppServer for an existing OpenEdXInstance

        Must pass a parameter called 'instance_id' which is the ID of the InstanceReference of
        the OpenEdXInstance that this AppServer is for.
        """
        if self.request.user.is_superuser:
            default_deployment_type = DeploymentType.admin.name
        else:
            default_deployment_type = DeploymentType.user.name
        # Allow overriding deployment type in case deployment is created by API in some other way.
        deployment_type = request.query_params.get("deployment_type", default_deployment_type)
        serializer = SpawnAppServerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        instance_id = serializer.validated_data['instance_id']

        # Limit by organization. Instance managers can't spawn servers for other organizations
        filtered_instances = IsOrganizationOwnerFilterBackendInstance().filter_queryset(
            request,
            InstanceReference.objects.all(),
            view=None,
        )

        try:
            instance_ref = filtered_instances.get(pk=instance_id)
        except ObjectDoesNotExist:
            raise NotFound('InstanceReference with ID {} not found.'.format(instance_id))

        instance = instance_ref.instance
        if not isinstance(instance, OpenEdXInstance):
            raise serializers.ValidationError('Invalid InstanceReference ID: Not an OpenEdXInstance.')

        create_new_deployment(
            instance,
            creator=self.request.user,
            deployment_type=deployment_type,
        )
        return Response({'status': 'Instance provisioning started'})

    @action(detail=True, methods=['get'])
    def logs(self, request, pk):
        """
        Get this AppServer's log entries
        """
        return Response(OpenEdXAppServerLogSerializer(self.get_object()).data)

    @action(detail=True, methods=['post'])
    def make_active(self, request, pk):
        """
        Add this AppServer to the list of active app server for the instance.
        """
        app_server = self.get_object()
        if not app_server.status.is_healthy_state or not make_appserver_active(app_server.pk):
            return Response(
                {"error": "Cannot make an unhealthy app server active."}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response({'status': 'App server activation initiated.'})

    @action(detail=True, methods=['post'])
    def make_inactive(self, request, pk):
        """
        Remove this AppServer from the list of active app server for the instance.
        """
        app_server = self.get_object()
        make_appserver_active(app_server.pk, active=False)
        return Response({'status': 'App server deactivation initiated.'})

    @action(detail=True, methods=['post'])
    def terminate(self, request, pk):
        """
        Trigger worker task to terminate the VM running the provided AppServer.

        Note that this might fail silently without any errors appearing on the Ocim UI,
        but it's acceptable given the current use case.
        """
        app_server = self.get_object()
        if app_server.is_active:
            return Response({
                'error': 'Cannot terminate an active app server.'
            }, status=status.HTTP_400_BAD_REQUEST)
        terminate_appserver(app_server.id)
        return Response({'status': 'App server termination initiated.'})


class OpenEdXReleaseViewSet(viewsets.ViewSet):
    """
    API to list all *unique* OpenEdxRelease (AppServer.openedx_release) instances.
    """
    permission_classes = [IsSuperUser]
    serializer_class = OpenEdXReleaseSerializer

    def list(self, request):
        """
        List API for all AppServer Statuses.
        """
        releases = OpenEdXAppServer.objects.values_list('openedx_release', flat=True)
        releases = releases.order_by('openedx_release').distinct()
        releases = ({'name': v} for v in releases if v)
        serializer = self.serializer_class(releases, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        """
        API to fetch and list single OpenEdxRelease (AppServer.openedx_release) instance.
        """
        releases = OpenEdXAppServer.objects.values_list('openedx_release', flat=True)
        release_name = releases.filter(openedx_release=pk).first()
        serializer = self.serializer_class({'name': release_name})
        return Response(serializer.data)
