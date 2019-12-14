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
Global URL Patterns
"""

# Imports #####################################################################

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView

from opencraft.utils import get_site_url
import opencraft.views as views

# URL Patterns ################################################################

urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include('api.urls', namespace='api')),
    url(r'^instance/', include('instance.urls', namespace='instance')),
    url(r'^registration/', include('registration.urls', namespace='registration')),
    url(r'^reports/', include('reports.urls', namespace='reports')),
    url(r'^email-verification/', include('email_verification.urls', namespace='email-verification')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon/favicon.ico', permanent=False)),
    url(r'^$', views.IndexView.as_view(), name='index'),
]

if settings.DEBUG and settings.ENABLE_DEBUG_TOOLBAR:
    # Enable debug toolbar URLs
    import debug_toolbar
    # "debug" URL pattern must be before "site" URL pattern.
    # See https://github.com/jazzband/django-debug-toolbar/issues/529
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
