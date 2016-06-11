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
Instance API
"""

# Imports #####################################################################

from rest_framework import viewsets

from instance.models.instance import InstanceReference
from instance.serializers.instance import InstanceReferenceBasicSerializer, InstanceReferenceDetailedSerializer


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
    * `created`
    * `modified`
    * `instance_type`

    Note that IDs used for instances are always the ID of the InstanceReference object, which
    may not be the same as the ID of the specific Instance subclass (e.g. the OpenEdXInstance
    object has its own ID which should never be used - just use its InstanceReference ID). This
    detail is managed by the API so users of the API should not generally need to be aware of
    it.
    """
    queryset = InstanceReference.objects.all()

    def get_serializer_class(self):
        """
        Return the basic serializer for the list action, and the detailed serializer otherwise.
        """
        if self.action == 'list':
            return InstanceReferenceBasicSerializer
        return InstanceReferenceDetailedSerializer

    def get_view_name(self):
        """
        Get the verbose name for each view
        """
        suffix = self.suffix
        if self.action == 'retrieve':
            suffix = "Details"
        return "Instance {}".format(suffix)
