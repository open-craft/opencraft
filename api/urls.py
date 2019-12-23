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
URL Patterns for api app
"""

# Imports #####################################################################

from django.conf.urls import include, url
from django.views.generic.base import RedirectView
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

from api.auth import JWTAuthToken
from api.router import v1_router, v2_router
from opencraft.swagger import api_info


# URL Patterns ################################################################

app_name = 'api'

# pylint: disable=invalid-name
schema_view = get_schema_view(
    info=api_info,
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='v1/', permanent=False), name='index'),
    # v1 urls
    url(r'^v1/', include((v1_router.urls, 'api_v1'), namespace='v1')),
    url(r'^v1/auth/', include('rest_framework.urls', namespace='rest_framework')),
    # v2 urls
    url(r'^v2/', include((v2_router.urls, 'api_v2'), namespace='v2')),
    url(r'^v2/auth/token/', JWTAuthToken.as_view(), name='token_obtain_pair'),
    # Documentation
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=10), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=10), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=10), name='schema-redoc'),
]
