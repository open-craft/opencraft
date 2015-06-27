# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
Global URL Patterns
"""

# Imports #####################################################################

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView


# URL Patterns ################################################################

urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('api.urls', namespace="api")),
    url(r'^instance/', include('instance.urls', namespace="instance")),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon/favicon.ico', permanent=False)),
    url(r'^$', 'instance.views.index'),
]
