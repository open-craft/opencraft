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
Instance serializers (API representation)
"""

# Imports #####################################################################

from rest_framework import serializers

from instance.models.instance import OpenEdXInstance
from instance.models.server import OpenStackServer


# Serializers #################################################################

class OpenStackServerSerializer(serializers.ModelSerializer):
    """
    OpenStackServer API Serializer
    """
    api_url = serializers.HyperlinkedIdentityField(view_name='api:openstackserver-detail')
    instance = serializers.HyperlinkedRelatedField(view_name='api:openedxinstance-detail', read_only=True)

    class Meta:
        model = OpenStackServer
        fields = (
            'id',
            'api_url',
            'created',
            'instance',
            'modified',
            'openstack_id',
            'status',
        )


class OpenEdXInstanceSerializer(serializers.ModelSerializer):
    """
    OpenEdXInstance API Serializer
    """
    api_url = serializers.HyperlinkedIdentityField(view_name='api:openedxinstance-detail')
    active_server_set = OpenStackServerSerializer(many=True, read_only=True)

    class Meta:
        model = OpenEdXInstance
        fields = (
            'id',
            'api_url',
            'active_server_set',
            'base_domain',
            'branch_name',
            'commit_id',
            'created',
            'domain',
            'email',
            'github_base_url',
            'github_branch_url', 'log_text',
            'github_organization_name',
            'modified',
            'name',
            'protocol',
            'repository_url',
            'status',
            'studio_url',
            'sub_domain',
            'url',
            'updates_feed',
            'vars_str',
        )
