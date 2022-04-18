# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <contact@opencraft.com>
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
The Grove app's API serializer.
"""

from rest_framework import serializers

from grove.models.deployment import GroveDeployment
from grove.models.instance import GroveInstance


class GroveDeploymentSerializer(serializers.ModelSerializer):
    """
    Model serializer for the Grove deployment.
    """

    class Meta:
        model = GroveDeployment
        fields = "__all__"


class GroveInstanceSerializer(serializers.ModelSerializer):
    """
    Model serializer for Grove instances.
    """
    class Meta:
        model = GroveInstance
        fields = "__all__"