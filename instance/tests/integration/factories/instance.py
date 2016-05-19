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
OpenEdXInstance model - Factories
"""

# Imports #####################################################################

import uuid

import factory
from factory.django import DjangoModelFactory

from instance.models.openedx_instance import OpenEdXInstance


# Classes #####################################################################

class OpenEdXInstanceFactory(DjangoModelFactory):
    """
    Factory for OpenEdXInstance
    """
    class Meta:
        model = OpenEdXInstance

    sub_domain = factory.LazyAttribute(lambda o: '{}.integration'.format(str(uuid.uuid4())[:8]))
    name = factory.Sequence('Test Instance {}'.format)
    openedx_release = 'named-release/cypress' # Use a known working version
    configuration_source_repo_url = 'https://github.com/open-craft/configuration.git'
    configuration_version = 'integration'
    # The open-craft fork doesn't have the 'named-release/cypress' tag, so use upstream:
    edx_platform_repository_url = 'https://github.com/edx/edx-platform.git'
    use_ephemeral_databases = True
