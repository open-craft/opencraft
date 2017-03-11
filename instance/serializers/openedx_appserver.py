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
Open edX AppServer serializers (API representation)
"""

# Imports #####################################################################

from rest_framework import serializers

from instance.models.openedx_appserver import OpenEdXAppServer, OpenEdXAppConfiguration
from instance.serializers.appserver import AppServerBasicSerializer
from instance.serializers.instance import InstanceReferenceMinimalSerializer
from instance.serializers.logentry import LogEntrySerializer
from instance.serializers.server import OpenStackServerSerializer

# Serializers #################################################################


class OpenEdXAppServerSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for OpenEdXAppServer
    """
    instance = InstanceReferenceMinimalSerializer(source='owner')
    server = OpenStackServerSerializer()

    class Meta:
        model = OpenEdXAppServer
        fields = tuple(OpenEdXAppConfiguration.get_config_fields()) + (
            'configuration_database_settings',
            'configuration_storage_settings',
            'configuration_settings',
            'instance',
            'server',
        )

    def to_representation(self, obj):
        """
        Add additional fields/data to the output
        """
        output = AppServerBasicSerializer(obj, context=self.context).data
        output.update(super().to_representation(obj))
        return output


class OpenEdXAppServerLogSerializer(serializers.ModelSerializer):
    """
    Provide the log entries for an OpenEdXAppServer
    """
    log_entries = LogEntrySerializer(many=True, read_only=True)
    log_error_entries = LogEntrySerializer(many=True, read_only=True)

    class Meta:
        model = OpenEdXAppServer
        fields = ('log_entries', 'log_error_entries')


# create/update intentionally omitted, pylint: disable=abstract-method
class SpawnAppServerSerializer(serializers.Serializer):
    """
    Serializer for the 'instance_id' argument to the "POST .../spawn/" view
    """
    instance_id = serializers.IntegerField(label="Open edX Instance ID")

    class Meta:
        fields = ('instance_id', )
