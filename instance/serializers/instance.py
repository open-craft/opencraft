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
Instance serializers (API representation)
"""

# Imports #####################################################################

from rest_framework import serializers

from instance.models.instance import InstanceReference, Instance
from instance.models.openedx_instance import OpenEdXInstance
from instance.serializers.logentry import LogEntrySerializer
from instance.serializers.openedx_instance import OpenEdXInstanceSerializer


# Serializers #################################################################


class InstanceReferenceMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer for InstanceReference that includes only the ID and URL.
    """
    api_url = serializers.HyperlinkedIdentityField(view_name='api:instance-detail')

    class Meta:
        model = InstanceReference
        fields = (
            'id',
            'api_url',
        )


class InstanceReferenceBasicSerializer(InstanceReferenceMinimalSerializer):
    """
    Serializer for InstanceReference that includes additional information based on the Instance
    subclass linked to the InstanceReference.

    InstanceReference is a simple class that points to all the concrete 'Instance' subclasses
    such as OpenEdXInstance.
    """

    # summary_only: Uses less detailed serializers for related instances
    summary_only = True

    class Meta:
        model = InstanceReference
        fields = (
            'id',
            'api_url',
            'name',
            'created',
            'modified',
        )

    def serialize_details(self, instance):
        """
        Given an object that is a subclass of Instance, serialize it.
        """
        if not isinstance(instance, Instance):
            raise TypeError("InstanceReference.instance should return a subclass of Instance")

        # Use the correct serializer for this type of Instance:
        if isinstance(instance, OpenEdXInstance):
            serializer = OpenEdXInstanceSerializer
        else:
            raise NotImplementedError("No serializer enabled for that Instance type.")

        if self.summary_only and hasattr(serializer, 'basic_serializer'):
            serializer = serializer.basic_serializer

        return serializer(instance, context=self.context).data

    def to_representation(self, obj):
        """
        Add additional fields/data to the output
        """
        output = super().to_representation(obj)
        output['instance_type'] = obj.instance_type.model
        details = self.serialize_details(obj.instance)
        # Merge instance details into the resulting dict, but never overwrite existing fields
        for key, val in details.items():
            output.setdefault(key, val)
        if not self.summary_only:
            # Add log entries:
            output['log_entries'] = [LogEntrySerializer(entry).data for entry in obj.instance.log_entries]
        return output


class InstanceReferenceDetailedSerializer(InstanceReferenceBasicSerializer):
    """
    Serializer for InstanceReference that is like InstanceReferenceBasicSerializer but includes
    more detail.
    """
    summary_only = False
