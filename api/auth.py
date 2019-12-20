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
JWT Auth overrides to generate swagger models
"""
# pylint: disable=abstract-method,arguments-differ,missing-docstring

from drf_yasg.utils import swagger_auto_schema
from rest_framework import serializers

from rest_framework_simplejwt.views import TokenObtainPairView


class TokenSerializer(serializers.Serializer):
    """
    Token Serializer - for swagger

    This overrides the serializer returned by the JSON library and
    fixes the generated swagger schema.
    Desired return format:
    {
        "access": "<TOKEN>",
        "refresh": "<TOKEN>",
    }
    """
    refresh = serializers.CharField()
    access = serializers.CharField()


class TokenErrorSerializer(serializers.Serializer):
    """
    Token Error Serializer - for swagger

    This overrides the serializer returned by the JSON library and
    fixes the generated swagger schema.
    Desired return format:
    {
        "details": "error"
    }
    """
    details = serializers.CharField()


class JWTAuthToken(TokenObtainPairView):
    """
    JWTAuthToken - for swagger

    This overrides the method just to add the Swagger schema overrides
    """
    @swagger_auto_schema(responses={201: TokenSerializer, 491: TokenErrorSerializer})
    def post(self, *args, **kwargs):
        return super(JWTAuthToken, self).post(*args, **kwargs)
