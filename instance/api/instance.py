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
Instance API
"""

# Imports #####################################################################
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from instance.models.instance import InstanceReference
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.serializers.instance import (
    InstanceReferenceBasicSerializer,
    InstanceReferenceDetailedSerializer,
    InstanceLogSerializer,
    InstanceAppServerSerializer
)

from .filters import IsOrganizationOwnerFilterBackendInstance


# Views - API #################################################################


class InstanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to list and manipulate instances.

    Uses InstanceReference to iterate all types of instances, and serializes them.

    The fields that are returned for each instance depend on its instance_type and whether you
    are listing all instances (returns fewer fields) or just one instance (returns all fields).

    The only fields that are available for all instances, regardless of type, are the fields
    defined on the InstanceReference class, namely:

    * `id`
    * `name`
    * `notes`
    * `created`
    * `modified`
    * `instance_type`
    * `is_archived`

    Note that IDs used for instances are always the ID of the InstanceReference object, which
    may not be the same as the ID of the specific Instance subclass (e.g. the OpenEdXInstance
    object has its own ID which should never be used - just use its InstanceReference ID). This
    detail is managed by the API so users of the API should not generally need to be aware of
    it.
    """
    queryset = InstanceReference.objects.all()
    serializer_class = InstanceReferenceDetailedSerializer
    filter_backends = (IsOrganizationOwnerFilterBackendInstance,)

    def get_queryset(self):
        # Don't load all columns, because some of them have very big data
        appservers_few_columns = OpenEdXAppServer.objects.only('_is_active', '_status', 'id', 'name', 'owner_id',
                                                               'created', 'modified', 'terminated')
        queryset = self.queryset.prefetch_related(
            # Use prefetching to make the number of database queries required to
            # generate this list O(1).
            # Note that prefetching all app servers information is still required, as the "newest" is not decideable
            # at this point. This will cause more data than necessary to be streamed from the DB, but removing this
            # prefetch without first selecting only the "newest" here results in O(n).
            Prefetch(
                'instance__ref_set__openedxappserver_set',
                queryset=appservers_few_columns,
            ),
            Prefetch(
                'instance__ref_set__openedxappserver_set',
                queryset=appservers_few_columns.filter(_is_active=True),
                to_attr='_cached_active_appservers'
            ),
        )
        return queryset

    def list(self, request, *args, **kwargs):
        """
        List all instances. No App server list is returned in the list view, only the newest app server information.

        """
        queryset = self.filter_queryset(self.get_queryset())
        if 'include_archived' not in request.query_params:
            # By default, exclude archived instances from the list:
            queryset = queryset.filter(is_archived=False)
        serializer = InstanceReferenceBasicSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def logs(self, request, pk):
        """
        Get this Instance's log entries
        """
        return Response(InstanceLogSerializer(self.get_object()).data)

    @detail_route(methods=['get'])
    def app_servers(self, request, pk):
        """
        Get this Instance's entire list of AppServers
        """
        return Response(InstanceAppServerSerializer(self.get_object(), context={'request': request}).data)

    @detail_route(methods=['post'])
    def set_notes(self, request, pk):
        """
        Update notes attribute of selected instance.
        """
        if not request.user.is_staff:
            return Response(
                {"error": "You do not have permissions to edit this field."},
                status=status.HTTP_403_FORBIDDEN
            )
        if 'notes' not in request.data:
            return Response({'status': 'No notes value provided.'})

        instance = InstanceReferenceBasicSerializer(self.get_object(),
                                                    context={'request': request},
                                                    data={'notes': request.data['notes']},
                                                    partial=True)
        if instance.is_valid():
            instance.save()
            return Response({'status': 'Instance attributes updated.'})
        else:
            return Response(
                {"error": "Instance attributes are not valid."},
                status=status.HTTP_400_BAD_REQUEST
            )
