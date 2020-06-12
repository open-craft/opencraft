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
REST Framework API - Router
"""

# Imports #####################################################################

from rest_framework import routers

from email_verification.api.v2.views import VerifyEmailViewset
from instance.api.instance import InstanceViewSet
from instance.api.openedx_appserver import OpenEdXAppServerViewSet
from instance.api.server import OpenStackServerViewSet
from pr_watch.api import WatchedPullRequestViewSet
from registration.api.v2.views import (
    AccountViewSet,
    OpenEdXInstanceConfigViewSet,
    OpenEdxInstanceDeploymentViewSet,
)

# Router ######################################################################

v1_router = routers.DefaultRouter()

v1_router.register(r'instance', InstanceViewSet, base_name='instance')
v1_router.register(r'openedx_appserver', OpenEdXAppServerViewSet)
v1_router.register(r'openstackserver', OpenStackServerViewSet)
v1_router.register(r'pr_watch', WatchedPullRequestViewSet, base_name='pr_watch')

v2_router = routers.DefaultRouter()
v2_router.register(r'accounts', AccountViewSet, base_name='accounts')
v2_router.register(r'instances/openedx_config', OpenEdXInstanceConfigViewSet, base_name='openedx-instance-config')
v2_router.register(
    r'instances/openedx_deployment',
    OpenEdxInstanceDeploymentViewSet,
    base_name='openedx-instance-deployment'
)
v2_router.register(r'verify_email', VerifyEmailViewset, base_name='verify-email-api')
