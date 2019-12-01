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
Swagger tools for OCIM.
"""
from drf_yasg import openapi
from rest_framework.settings import api_settings

GENERIC_ERROR = openapi.Schema(
    'Generic API Error',
    type=openapi.TYPE_OBJECT,
    properties={
        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
            'detail': openapi.Schema(type=openapi.TYPE_STRING, description='Error details'),
            'code': openapi.Schema(type=openapi.TYPE_STRING, description='Error code'),
        })
    },
    required=['detail']
)

ACCESS_ERROR_RESPONSE = openapi.Response(
    description="Authentication credentials were invalid, absent or insufficient.",
    schema=GENERIC_ERROR,
)

VALIDATION_ERROR = openapi.Schema(
    'Validation Error',
    type=openapi.TYPE_OBJECT,
    properties={
        'errors': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            description='error messages for each field that triggered a validation error',
            additional_properties=openapi.Schema(
                description='A list of error messages for the field',
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
            )),
        api_settings.NON_FIELD_ERRORS_KEY: openapi.Schema(
            description='List of validation errors not related to any field',
            type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING)
        ),
    }
)

VALIDATION_ERROR_RESPONSE = openapi.Response(
    description='Invalid data provided to API',
    schema=VALIDATION_ERROR,
)
