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
from urllib.parse import urljoin
from rest_framework import serializers

from grove.models.deployment import GroveDeployment
from grove.models.instance import GroveInstance
from grove.models.repository import GroveClusterRepository


class GroveClusterRepositorySerializer(serializers.ModelSerializer):
    """
    Model serializer for Grove cluster repositories.
    """

    class Meta:
        model = GroveClusterRepository
        fields = ["name", "project_id", "git_ref", "git_repo_url"]


class GroveDeploymentSerializer(serializers.ModelSerializer):
    """
    Model serializer for the Grove deployment.
    """

    def get_status(self, obj):
        """
        Return the name of the status.
        """
        return GroveDeployment.STATUS_NAMES[obj.status]

    def get_pipeline(self, obj):
        """
        Return the GitLab Pipeline URL for the deployment.
        """
        instance = obj.instance.instance
        pipeline = obj.pipeline

        if not instance or not pipeline:
            return ""

        return urljoin(f"{instance.repository.git_repo_url}/", f"-/pipelines/{pipeline.pipeline_id}")

    status = serializers.SerializerMethodField()
    pipeline = serializers.SerializerMethodField()

    class Meta:
        model = GroveDeployment
        fields = ("id", "status", "created", "modified", "overrides", "instance", "pipeline", )


class GroveInstanceSerializer(serializers.ModelSerializer):
    """
    Model serializer for Grove instances.
    """

    def get_deployments(self, obj):
        """
        Serialize and return deployments belonging to the instance.
        """
        deployments = GroveDeployment.objects.filter(instance=obj.ref)
        serializer = GroveDeploymentSerializer(deployments, many=True)
        return serializer.data

    deployments = serializers.SerializerMethodField()
    repository = GroveClusterRepositorySerializer(read_only=True)

    class Meta:
        model = GroveInstance
        fields = "__all__"
