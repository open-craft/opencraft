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

from instance.models.openedx_instance import OpenEdXInstance
from instance.serializers.appserver import AppServerBasicSerializer
from pr_watch.models import WatchedPullRequest
from pr_watch.serializers import WatchedPullRequestSerializer


# Serializers #################################################################


class OpenEdXInstanceBasicSerializer(serializers.ModelSerializer):
    """
    Simple high-level serializer for OpenEdXInstance
    """
    class Meta:
        model = OpenEdXInstance
        fields = (
            'domain',
            'is_shut_down',
        )

    def to_representation(self, obj):
        """
        Add additional fields/data to the output
        """
        output = super().to_representation(obj)
        output['appserver_count'] = obj.appserver_set.count()
        output['active_appserver'] = AppServerBasicSerializer(obj.active_appserver, context=self.context).data
        newest_appserver = obj.appserver_set.order_by('-created').first()
        output['newest_appserver'] = AppServerBasicSerializer(newest_appserver, context=self.context).data
        return output


class OpenEdXInstanceSerializer(OpenEdXInstanceBasicSerializer):
    """
    Detailed serializer for OpenEdXInstance
    """
    basic_serializer = OpenEdXInstanceBasicSerializer

    class Meta:
        model = OpenEdXInstanceBasicSerializer.Meta.model
        fields = OpenEdXInstanceBasicSerializer.Meta.fields + (
            'email',
            'use_ephemeral_databases',
            'github_admin_organizations',
            'github_admin_users',
            'active_appserver',
            'internal_lms_domain',
            'url',
            'studio_url',

            'http_auth_user',
            'http_auth_pass',

            'mysql_user',
            'mysql_pass',
            'mysql_provisioned',
            'mongo_user',
            'mongo_pass',
            'mongo_provisioned',

            'swift_openstack_user',
            'swift_openstack_password',
            'swift_openstack_tenant',
            'swift_openstack_auth_url',
            'swift_openstack_region',
            'swift_provisioned',
            's3_access_key',
            's3_secret_access_key',
            's3_bucket_name',

            'additional_security_groups',

            'configuration_source_repo_url',
            'configuration_version',
            'configuration_extra_settings',
            'edx_platform_repository_url',
            'edx_platform_commit',

            'openedx_release',
        )

    def to_representation(self, obj):
        """
        Add additional fields/data to the output
        """
        output = super().to_representation(obj)
        output['appservers'] = [
            AppServerBasicSerializer(appserver, context=self.context).data for appserver in obj.appserver_set.all()
        ]
        try:
            output['source_pr'] = WatchedPullRequestSerializer(obj.watchedpullrequest).data
        except WatchedPullRequest.DoesNotExist:
            output['source_pr'] = None
        if obj.load_balancing_server:
            output['load_balancing_server'] = obj.load_balancing_server.domain
        else:
            output['load_balancing_server'] = None
        return output
