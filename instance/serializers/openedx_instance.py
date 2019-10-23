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

from django.conf import settings
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
    domain = serializers.CharField(read_only=True)

    class Meta:
        model = OpenEdXInstance
        fields = (
            'domain',
        )

    def to_representation(self, instance):
        """
        Add additional fields/data to the output
        """
        output = super().to_representation(instance)
        output['appserver_count'] = instance.appserver_set.count()
        output['status_description'] = []

        # Store the list of active appservers, and collated status information
        #
        # * Instance is_healthy/_steady iff there's more than one active appserver,
        #   and all of the active appservers are healthy/steady.
        # * Instance status description is all the active appserver's status descriptions
        output['active_appservers'] = []
        output['status_description'] = []
        output['is_healthy'] = True
        output['is_steady'] = True
        for appserver in instance.get_active_appservers():
            serialized_appserver = AppServerBasicSerializer(appserver, context=self.context).data
            if not serialized_appserver['is_healthy']:
                output['is_healthy'] = False
            if not serialized_appserver['is_steady']:
                output['is_steady'] = False
            output['active_appservers'].append(serialized_appserver)
            output['status_description'].append(serialized_appserver['status_description'])

        output['status_description'] = '\n'.join(output['status_description'])
        if not output['active_appservers']:
            output['is_healthy'] = None
            output['is_steady'] = None

        try:
            # Note that appservers are ordered by '-created' by default.
            # We don't change or check the ordering of the .appserver_set.all() queryset here
            # because that causes the django ORM to force a new database query to be made
            # for each instance here, even if appserver_set was previously cached.
            newest_appserver = instance.appserver_set.all()[0]
        except IndexError:
            output['newest_appserver'] = None
        else:
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
            'deploy_simpletheme',
            'creator_username',
            'owner_organization',
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
            'rabbitmq_provisioned',

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
            'additional_monitoring_emails',
            'provision_failed_emails',

            'configuration_source_repo_url',
            'configuration_version',
            'configuration_extra_settings',
            'configuration_playbook_name',
            'edx_platform_repository_url',
            'edx_platform_commit',

            'openedx_release',

            'openstack_region',
            'openstack_server_flavor',
            'openstack_server_base_image',
            'openstack_server_ssh_keyname',

            'periodic_builds_enabled',
            'periodic_builds_interval',
            'periodic_builds_retries',
            'admin_url',
        )

    def to_representation(self, instance):
        """
        Add additional fields/data to the output
        """
        output = super().to_representation(instance)

        filtered_appservers = instance.appserver_set.all()[:settings.NUM_INITIAL_APPSERVERS_SHOWN]
        output['appservers'] = [
            AppServerBasicSerializer(appserver, context=self.context).data for appserver in filtered_appservers
        ]

        try:
            output['source_pr'] = WatchedPullRequestSerializer(instance.watchedpullrequest).data
        except WatchedPullRequest.DoesNotExist:
            output['source_pr'] = None

        if instance.load_balancing_server:
            output['load_balancing_server'] = instance.load_balancing_server.domain
        else:
            output['load_balancing_server'] = None

        output['configuration_theme_settings'] = instance.get_theme_settings()

        return output
