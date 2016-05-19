# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
REST Framework API - Router
"""

# Imports #####################################################################

from rest_framework import routers

from instance.api.instance import InstanceViewSet
from instance.api.openedx_appserver import OpenEdXAppServerViewSet
from instance.api.server import OpenStackServerViewSet
from betatest.api import BetaTestApplicationViewSet
from pr_watch.api import WatchedPullRequestViewSet


# Router ######################################################################

router = routers.DefaultRouter()

router.register(r'instance', InstanceViewSet, base_name='instance')
router.register(r'openedx_appserver', OpenEdXAppServerViewSet)
router.register(r'openstackserver', OpenStackServerViewSet)
router.register(r'beta/register/validate', BetaTestApplicationViewSet, base_name='register')
router.register(r'pr_watch', WatchedPullRequestViewSet, base_name='pr_watch')
