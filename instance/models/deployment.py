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
Instance app models - Deployment
"""

# Imports #####################################################################

from enum import Enum
import logging

from django.db import models
from django_extensions.db.models import TimeStampedModel

from userprofile.models import UserProfile
from .instance import InstanceReference

# Logging #####################################################################

logger = logging.getLogger(__name__)


# Enums #######################################################################

class DeploymentType(Enum):
    """Enumeration of all types of deployments"""
    user = 'Deployment initiated by user'
    batch = 'Deployment created by batch redeplpoyment script'
    admin = 'Deployment initiated by Ocim admin user'
    pr = 'Deployment for GitHub PR'
    periodic = 'Deployment for periodic build'
    registration = 'Deployment created during registration'
    unknown = 'Deployment created unknown or legacy reasons'

    def __str__(self):
        return self.name

    @classmethod
    def choices(cls):
        """Render enum as tuple to use in Django choice field"""
        return tuple((prop.name, prop.value) for prop in cls)


# Models ######################################################################


class Deployment(TimeStampedModel):
    """
    Tracks deployments of AppServers.
    """

    # The Instance connected to this deployment
    instance = models.ForeignKey(InstanceReference, on_delete=models.CASCADE)
    # The creator of this deployment
    creator = models.ForeignKey(UserProfile, null=True, on_delete=models.CASCADE)
    # The reason for triggering this deployment
    type = models.CharField(
        max_length=10,
        choices=DeploymentType.choices(),
        default=DeploymentType.unknown,
    )

    class Meta:
        ordering = ('-created',)
