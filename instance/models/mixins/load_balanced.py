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
Instance app model mixins - load balancing
"""

# Imports #####################################################################

from django.db import models
from django.conf import settings

from instance.models.load_balancer import LoadBalancingServer


# Functions ###################################################################

def get_preliminary_page_config(primary_key, domain_names):
    """Return a load balancer configuration for the preliminary page."""
    if not settings.PRELIMINARY_PAGE_SERVER_IP:
        return [], []
    backend_name = "be-preliminary-page-{}".format(primary_key)
    config = "    server preliminary-page {}:80".format(settings.PRELIMINARY_PAGE_SERVER_IP)
    backend_map = [(domain, backend_name) for domain in domain_names if domain]
    return backend_map, [(backend_name, config)]


# Classes #####################################################################

class LoadBalancedInstance(models.Model):
    """
    Mixin for load-balanced instances.
    """
    load_balancing_server = models.ForeignKey(LoadBalancingServer, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        abstract = True
