# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <contact@opencraft.com>
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
The Grove deployment model.
"""

import logging

from django.contrib.contenttypes import fields
from django.db import models

from grove.models.repository import GroveClusterRepository, get_default_repository
from instance.models.instance import Instance, InstanceTag
from instance.models.mixins.domain_names import DomainNameInstance
from instance.models.mixins.openedx_monitoring import OpenEdXMonitoringMixin
from instance.models.mixins.openedx_site_configuration import OpenEdXSiteConfigurationMixin
from instance.models.mixins.openedx_static_content_overrides import OpenEdXStaticContentOverridesMixin
from instance.models.mixins.openedx_storage import OpenEdXStorageMixin
from instance.models.mixins.openedx_theme import OpenEdXThemeMixin
from instance.models.openedx_appserver import OpenEdXAppConfiguration

# from registration.models import BetaTestApplication

logger = logging.getLogger(__name__)


class GroveInstance(
    DomainNameInstance,
    OpenEdXAppConfiguration,
    OpenEdXMonitoringMixin,
    OpenEdXSiteConfigurationMixin,
    OpenEdXStaticContentOverridesMixin,
    OpenEdXStorageMixin,
    OpenEdXThemeMixin,
    Instance,
):
    """
    GroveInstance contains the mandatory field values for an instance.

    Although Grove and Tutor handles the configuration for instances, we must
    know some parameters about instances to provide better user experience and
    do not create duplicated instances over time.

    Since the configuration of instances shall happen through PRs against the
    corresponding Grove repository, this model contains only the those fields
    that are mandatory -- please keep this in mind all the time you work with
    this model.

    This model is updated by webhooks and shall not be updated manually. If
    the manual modification is a must-have, a double bookkeeping is required
    in the corresponding Grove repository as well to keep it in sync.

    GroveInstance model is derived from the Instance model.
    """
    betatestapplication = fields.GenericRelation('registration.BetaTestApplication', content_type_field='instance_type', object_id_field='instance_id')
    tags = models.ManyToManyField(
        InstanceTag,
        blank=True,
        help_text='Custom tags associated with the instance.',
    )
    repository = models.ForeignKey(
        GroveClusterRepository,
        default=get_default_repository,
        on_delete=models.SET_NULL,
        null=True,
        help_text='Repository in GitLab in which the instance is defined.'
    )

    successfully_provisioned = models.BooleanField(default=False)

    def get_latest_deployment(self):
        """ The latest GroveDeployment associated with this instance. """
        deployment = super(GroveInstance, self).get_latest_deployment()
        if deployment:
            return deployment.grovedeployment
        return None
