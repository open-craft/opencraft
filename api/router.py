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
from grove.api.v1.views import GroveDeploymentAPIView
from instance.api.appserver import StatusViewSet
from instance.api.deployment import DeploymentTypeViewSet
from instance.api.instance import InstanceViewSet, InstanceTagViewSet
from instance.api.openedx_appserver import OpenEdXAppServerViewSet, OpenEdXReleaseViewSet
from instance.api.server import OpenStackServerViewSet

from pr_watch.api import WatchedPullRequestViewSet
from registration.api.v2.views import (
    AccountViewSet,
    NotificationsViewSet,
    OpenEdXInstanceConfigViewSet,
    OpenEdxInstanceDeploymentViewSet,
)

# Router ######################################################################

v1_router = routers.DefaultRouter()

v1_router.register(r'status', StatusViewSet, basename='status')
v1_router.register(r'deployment_type', DeploymentTypeViewSet, basename='deployment_type')
v1_router.register(r'grove/deployments', GroveDeploymentAPIView, basename='grove-deployments')
v1_router.register(r'instance', InstanceViewSet, basename='instance')
v1_router.register(r'instance_tag', InstanceTagViewSet, basename='instance_tag')
v1_router.register(r'openedx_appserver', OpenEdXAppServerViewSet)
v1_router.register(r'openedx_release', OpenEdXReleaseViewSet, basename='openedx_release')
v1_router.register(r'openstackserver', OpenStackServerViewSet)
v1_router.register(r'pr_watch', WatchedPullRequestViewSet, basename='pr_watch')

v2_router = routers.DefaultRouter()
v2_router.register(r'accounts', AccountViewSet, basename='accounts')
v2_router.register(r'instances/openedx_config', OpenEdXInstanceConfigViewSet, basename='openedx-instance-config')
v2_router.register(
    r'instances/openedx_deployment',
    OpenEdxInstanceDeploymentViewSet,
    basename='openedx-instance-deployment'
)
v2_router.register(
    r'notifications',
    NotificationsViewSet,
    basename='notifications'
)
v2_router.register(r'verify_email', VerifyEmailViewset, basename='verify-email-api')
