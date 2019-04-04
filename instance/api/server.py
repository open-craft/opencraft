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
Instance views
"""

# Imports #####################################################################

from rest_framework import viewsets

from instance.api.permissions import IsSuperUser
from instance.models.server import OpenStackServer
from instance.serializers.server import OpenStackServerSerializer


# Views #######################################################################

class OpenStackServerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This API allows you retrieve information about OpenStackServer objects (OpenStack VMs).
    It is visible only to superusers because if we open it to instance managers we need to filter
    VMs by organization. Since this API isn't used by the UI, for now we keep it internal and superuser only.
    """
    queryset = OpenStackServer.objects.all()
    serializer_class = OpenStackServerSerializer
    permission_classes = [IsSuperUser]
