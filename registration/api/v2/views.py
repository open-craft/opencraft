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
from typing import List

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from opencraft.swagger import ACCESS_ERROR_RESPONSE, VALIDATION_ERROR_RESPONSE
from registration.api.v1.views import BetaTestApplicationMixin
from registration.api.v2.serializers import ReadCreateRegistrationSerializer, UpdateOnlyRegistrationSerializer

logger = logging.getLogger(__name__)


class RegistrationViewSet(BetaTestApplicationMixin, ViewSet):
    """
    ViewSet for user registration data.
    """

    def get_permissions(self) -> List[BasePermission]:
        """
        Use different permissions for different actions.
        """
        if self.action in ('create', 'validate'):
            # For registering or validating the registration we leave the permissions open.
            permission_classes = [AllowAny]
        else:
            # For other actions, such as viewing or updating the registration, we
            # need authentication
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Registration info for current user', ReadCreateRegistrationSerializer),
            403: ACCESS_ERROR_RESPONSE,
        }
    )
    def list(self, request: Request):
        """
        Get current user registration.

        Get registration data for currently logged-in user. This includes the user's
        profile information, and Open edX instance configuration.
        """
        return Response(
            ReadCreateRegistrationSerializer({
                'account': request.user.profile,
                'instance': self.get_object()
            }).data
        )

    @swagger_auto_schema(
        responses={
            201: openapi.Response('Account successfully registered.', ReadCreateRegistrationSerializer),
            400: VALIDATION_ERROR_RESPONSE,
        }
    )
    def create(self, request: Request):
        """
        Create new user registration.

        Set up a new registration for a user by creating a new user object, a new user
        profile and a new instance configuration.
        """

        serializer = ReadCreateRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={
            202: openapi.Response('Registration data successfully updated.'),
            400: VALIDATION_ERROR_RESPONSE,
            403: ACCESS_ERROR_RESPONSE,
        }
    )
    @action(detail=False, url_path='update', methods=['patch'])
    def update_registration(self, request: Request):
        """
        Update existing registration.

        Updates the registration data for the current user.
        """

        logger.info(request.data)
        serializer = UpdateOnlyRegistrationSerializer(
            instance={
                'account': request.user.profile,
                'instance': request.user.betatestapplication,
            },
            data=request.data,
            partial=True,
            context={
                'user': request.user
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Registration data successfully validated.', ReadCreateRegistrationSerializer),
            400: VALIDATION_ERROR_RESPONSE,
        }
    )
    @action(detail=False, methods=['post'])
    def validate(self, request: Request):
        """
        Validate registration data.

        Validate registration data without committing it to database.
        """
        serializer = ReadCreateRegistrationSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
