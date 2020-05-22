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
Email verification API
"""

from drf_yasg.utils import swagger_auto_schema
from rest_framework import (
    serializers,
    status,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import RetrieveModelMixin

from simple_email_confirmation.exceptions import EmailConfirmationExpired
from simple_email_confirmation.models import EmailAddress
from opencraft.swagger import (
    VALIDATION_AND_AUTH_RESPONSES,
    viewset_swagger_helper,
)


@viewset_swagger_helper(
    retrieve="Activate a user email.",
    public_actions=["retrieve"],
)
class VerifyEmailViewset(RetrieveModelMixin, GenericViewSet):
    """
    Public view used by the frontend to activate email addresses.
    """
    authentication_classes = []
    permission_classes = [AllowAny]
    # We don't need a queryset or serializer
    queryset = ''
    serializer_class = serializers.Serializer

    @swagger_auto_schema(
        serializer_class={},
        responses={**VALIDATION_AND_AUTH_RESPONSES},
        security=[],
    )
    # pylint: disable=arguments-differ
    def retrieve(self, request, pk=None):
        """
        Return a list of all users.
        """
        try:
            EmailAddress.objects.confirm(pk).email

        except EmailAddress.DoesNotExist:
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        except EmailConfirmationExpired:
            return Response(
                {
                    'non_field_errors': 'Email confirmation code expired.'
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({}, status=status.HTTP_200_OK)
