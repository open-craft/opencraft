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
API views for the Grove app.
"""

from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, CreateModelMixin
from rest_framework.permissions import IsAuthenticated

from grove.models.deployment import GroveDeployment
from grove.serializers import GroveDeploymentSerializer
from opencraft.swagger import viewset_swagger_helper


@viewset_swagger_helper(
    retrieve="Return a deployment",
    list="Return all deployments",
    create="Trigger new deployment in Grove for an existing instance",
    public_actions=["create"],
)
class GroveDeploymentAPIView(
    RetrieveModelMixin,
    ListModelMixin,
    CreateModelMixin,
    GenericViewSet
):
    """
    GroveDeploymentAPI is used to create new and monitor existing deployments.

    When an instance is created by a new customer or a deployment is needed to
    update the existing instance configuration, a new Deployment object is
    created. On creation GitLab will be notified and the appropriate GitLab
    pipeline is called to create a new or update an existing instance.
    """

    serializer_class = GroveDeploymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter the queryset based on user staff state.

        If the user is a staff user, return all deployments. Otherwise, return
        only those deployments that are related to the given user.
        """

        user = self.request.user

        if user.is_staff:
            return GroveDeployment.objects.all()

        return GroveDeployment.objects.filter(instance__creator__user=user)

