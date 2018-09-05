# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
from django.core.urlresolvers import reverse

from rest_framework import serializers


# Serializers #################################################################


# create/update intentionally omitted, pylint: disable=abstract-method
class AppServerBasicSerializer(serializers.BaseSerializer):
    """
    Simple high-level serializer for AppServer
    """
    def to_representation(self, obj):
        """
        Serialize AppServer object summary.

        This serializer will work with any subclass of the AppServer abstract class.
        """
        api_path = reverse('api:{}-detail'.format(obj._meta.model_name), kwargs={'pk': obj.pk})
        request = self.context.get('request')
        if request:
            api_url = request.build_absolute_uri(api_path)
        else:
            raise AssertionError("AppServerBasicSerializer should be instantiated with context={'request': request}")

        output = OrderedDict()
        output['id'] = obj.pk
        output['api_url'] = api_url
        output['name'] = obj.name
        output['is_active'] = obj.is_active

        output['status'] = obj.status.state_id
        output['status_name'] = obj.status.name
        output['status_description'] = obj.status.description
        # Add info about relevant conditions related to instance status:
        output['is_steady'] = obj.status.is_steady_state
        output['is_healthy'] = obj.status.is_healthy_state

        output['created'] = obj.created
        output['modified'] = obj.modified
        return output
