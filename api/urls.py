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
URL Patterns for api app
"""

# Imports #####################################################################

from django.conf.urls import include, url
from django.views.generic.base import RedirectView

from .router import router


# URL Patterns ################################################################

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='v1/', permanent=False), name='index'),
    url(r'^v1/', include(router.urls)),
    url(r'^v1/auth/', include('rest_framework.urls', namespace='rest_framework')),
]
