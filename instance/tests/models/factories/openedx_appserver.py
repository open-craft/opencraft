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
OpenEdXAppServer model - Factories
"""

# Imports #####################################################################

from instance.models.load_balancer import LoadBalancingServer
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory

# Functions ###################################################################


def make_test_appserver(instance=None, s3=False, server=None):
    """
    Factory method to create an OpenEdXAppServer (and OpenStackServer).
    """
    if not instance:
        instance = OpenEdXInstanceFactory()
    if not instance.load_balancing_server:
        instance.load_balancing_server = LoadBalancingServer.objects.select_random()
        instance.save()
    if s3:
        instance.s3_access_key = 'test'
        instance.s3_secret_access_key = 'test'
        instance.s3_bucket_name = 'test'
        instance.save()
    appserver = instance._create_owned_appserver()

    if server:
        appserver.server = server
        appserver.save()

    return appserver
