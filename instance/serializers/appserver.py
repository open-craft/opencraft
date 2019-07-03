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
Instance serializers (API representation)
"""

# Imports #####################################################################

from collections import OrderedDict
from django.urls import reverse

from rest_framework import serializers


# Serializers #################################################################


# create/update intentionally omitted, pylint: disable=abstract-method
class AppServerBasicSerializer(serializers.BaseSerializer):
    """
    Simple high-level serializer for AppServer
    """
    def to_representation(self, instance):
        """
        Serialize AppServer object summary.

        This serializer will work with any subclass of the AppServer abstract class.
        """

        api_path = reverse('api:{}-detail'.format(instance._meta.model_name), kwargs={'pk': instance.pk})
        request = self.context.get('request')
        if request:
            api_url = request.build_absolute_uri(api_path)
        else:
            raise AssertionError("AppServerBasicSerializer should be instantiated with context={'request': request}")

        output = OrderedDict()
        output['id'] = instance.pk
        output['api_url'] = api_url
        output['name'] = instance.name
        output['is_active'] = instance.is_active

        output['status'] = instance.status.state_id
        output['status_name'] = instance.status.name
        output['status_description'] = instance.status.description
        # Add info about relevant conditions related to instance status:
        output['is_steady'] = instance.status.is_steady_state
        output['is_healthy'] = instance.status.is_healthy_state

        output['created'] = instance.created
        output['modified'] = instance.modified
        output['terminated'] = instance.terminated
        return output
