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
from django.contrib.auth.decorators import login_required

from instance.models.instance import SingleVMOpenEdXInstance


# Functions - Helpers #########################################################

def get_context():
    """
    Commond context
    """
    instance_list = SingleVMOpenEdXInstance.objects.order_by('-created')

    context = {
        'instance_list': instance_list,
    }

    return context


# Views #######################################################################

@login_required
def index(request):
    """
    Index view
    """
    return render(request, 'instance/index.html', get_context())
