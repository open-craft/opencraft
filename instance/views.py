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
Instance views
"""

# Imports #####################################################################

from django.shortcuts import render
from rest_framework import viewsets

from .models import OpenStackServer, OpenEdXInstance
from .serializers import OpenStackServerSerializer, OpenEdXInstanceSerializer


# Functions - Helpers #########################################################

def get_context():
    instance_list = OpenEdXInstance.objects.order_by('-created')

    context = {
        'instance_list': instance_list,
    }

    return context


# Views #######################################################################

def index(request):
    return render(request, 'instance/index.html', get_context())


# Views - API #################################################################

class OpenStackServerViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = OpenStackServer.objects.all()
    serializer_class = OpenStackServerSerializer

class OpenEdXInstanceViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = OpenEdXInstance.objects.all()
    serializer_class = OpenEdXInstanceSerializer
