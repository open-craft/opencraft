# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Registration api views for API v2
"""
import logging

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from opencraft.swagger import viewset_swagger_helper
from registration.api.v2.serializers import AccountSerializer, OpenEdXInstanceConfigSerializer
from registration.models import BetaTestApplication
from registration.utils import verify_user_emails
from userprofile.models import UserProfile

logger = logging.getLogger(__name__)


@viewset_swagger_helper(
    create="Create new user registration",
    list="Get current user registration data",
    update="Update current user registration data",
    partial_update="Update current user registration data",
    public_actions=['create'],
    tags=["v1", "Accounts", "Registration", "User", "UserProfile"],
)
class AccountViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    User account management API.

    This API can be used to register users, and to access user registration
    information for the current user.
    """
    serializer_class = AccountSerializer

    def perform_update(self, serializer):
        """
        When a new user registers, initiate email verification.
        """
        instance = serializer.save()
        verify_user_emails(instance, self.request, instance.email)

    def perform_create(self, serializer):
        """
        If a user updates their profile, initiate email verification in case their
        email has changed.
        """
        instance = serializer.save()
        verify_user_emails(instance, self.request, instance.email)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            # Allow any user to create an account, but limit other actions to logged-in users.
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Get user profile objects restricted to the current user.
        Should be only one.
        """
        return UserProfile.objects.filter(user=self.request.user)


@viewset_swagger_helper(
    list="Get all instances owned by user",
    create="Create new user instance.",
    retrieve="Get an instance owned by user",
    update="Update instance owned by user",
    partial_update="Update instance owned by user",
    public_actions=['create'],
    tags=["v2", "Instances", "OpenEdXInstanceConfig"],
)
class OpenEdXInstanceConfigViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Open edX Instance Configuration API.

    This API can be used to manage the configuration for Open edX instances
    owned by clients.
    """
    serializer_class = OpenEdXInstanceConfigSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        """
        When a new instance is registered queue its public contact email for verification.
        """
        instance = serializer.save()
        verify_user_emails(instance.user, self.request, instance.public_contact_email)

    def perform_update(self, serializer):
        """
        If an instance has been changed, queuse its public contact email for verification
        if it has been changed.
        """
        instance = serializer.save()
        verify_user_emails(instance.user, self.request, instance.public_contact_email)


def get_queryset(self):
    """
    Get `BetaTestApplication` instances owned by current user.
    Currently this should return a single object.
    """
    return BetaTestApplication.objects.filter(user=self.request.user)
