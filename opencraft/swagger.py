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
from typing import Optional, Callable, List

from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
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

VALIDATION_AND_AUTH_RESPONSES = {
    status.HTTP_400_BAD_REQUEST: VALIDATION_ERROR_RESPONSE,
    status.HTTP_403_FORBIDDEN: ACCESS_ERROR_RESPONSE,
}

VALIDATION_RESPONSE = {
    status.HTTP_400_BAD_REQUEST: VALIDATION_ERROR_RESPONSE,
}


def viewset_swagger_helper(
        public_actions=None,
        tags: Optional[List[str]] = None,
        **action_summary_docs: Optional[str]
) -> Callable:
    """
    A meta-decorator to apply swagger decorators for multiple methods.

    This decorator simplifies applying multiple decorators by applying sane defaults
    for swagger decorator, and passing in the supplied values as the summary.

    Example:
        @viewset_swagger_helper(
            list="List Snippets",
            create="Create new Snippet",
            destroy="Delete Snippet",
            public_actions=["list"]
        )
        class SnippetViewSet(ModelViewSet): ...

        In the above example this function will apply a decorator that will override
        the operation summary for `list`, `create` and `destroy` for the `SnippetViewSet`.
        The `public_actions` parameter specifies which actions don't need an authentication
        and as such won't raise an authentication/authorization error.
    """
    decorators_to_apply = []
    public_actions = [] if public_actions is None else public_actions
    for action in ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']:
        if action in action_summary_docs:
            decorators_to_apply.append(
                method_decorator(
                    name=action,
                    decorator=swagger_auto_schema(
                        operation_summary=action_summary_docs.get(action),
                        responses=VALIDATION_RESPONSE if action in public_actions else VALIDATION_AND_AUTH_RESPONSES,
                        tags=tags,
                    ),
                )
            )

    def inner(viewset):
        """
        Applies all the decorators built up in the decorator list.
        """
        for decorator in decorators_to_apply:
            viewset = decorator(viewset)
        return viewset

    return inner
