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
URL Patterns for the `registration` app
"""

# Imports #####################################################################

from django.conf.urls import url
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView

from registration.forms import LoginForm
from registration.views import BetaTestApplicationView


# URL Patterns ################################################################

app_name = 'registration'
urlpatterns = [
    url(r'^$', BetaTestApplicationView.as_view(), name='register'),
    url(r'^login/$', LoginView.as_view(authentication_form=LoginForm), name='login'),
    url(r'^logout/$', LogoutView.as_view(next_page='/'), name='logout'),
    url(r'^terms/$', TemplateView.as_view(template_name='registration/terms.html'), name='terms'),
    url(r'^privacy/$', TemplateView.as_view(template_name='registration/privacy.html'), name='privacy'),
]
