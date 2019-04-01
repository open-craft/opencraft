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
OpenEdXInstance model - Factories
"""

# Imports #####################################################################

import uuid

import factory
from factory.django import DjangoModelFactory

from instance.models.mixins.domain_names import generate_internal_lms_domain
from instance.models.openedx_instance import OpenEdXInstance


# Classes #####################################################################

class OpenEdXInstanceFactory(DjangoModelFactory):
    """
    Factory for OpenEdXInstance
    """
    class Meta:
        model = OpenEdXInstance

    @classmethod
    def create(cls, *args, **kwargs):
        # OpenEdXInstance constructor accepts either a 'sub_domain' or 'instance_lms_domain' value. Only generate a
        # random value for 'internal_lms_domain' if neither 'sub_domain' nor 'internal_lms_domain' are provided.
        if 'sub_domain' not in kwargs and 'internal_lms_domain' not in kwargs:
            kwargs = kwargs.copy()
            random_id = str(uuid.uuid4())[:6]
            sub_domain = '{}.integration'.format(random_id)
            kwargs['random_prefix'] = random_id
            kwargs['internal_lms_domain'] = generate_internal_lms_domain(sub_domain)
        return super(OpenEdXInstanceFactory, cls).create(*args, **kwargs)

    name = factory.Sequence('Test Instance {}'.format)

    # Versions to use for the integration tests.  The field "openedx_release" must be a commit name
    # that is valid for the forums, notifier, xqueue and certs, so usually only an official release
    # or a release candidate tag will work.  We point both the edx-platform and the configuration
    # versions to the branch "integration" in our own forks.  These branches are based on the
    # corresponding openedx_release versions from upstream, but can contain custom modifications.
    openedx_release = 'open-release/hawthorn.1'
    configuration_source_repo_url = 'https://github.com/open-craft/configuration.git'
    configuration_version = 'integration-hawthorn'
    edx_platform_repository_url = 'https://github.com/open-craft/edx-platform.git'
    edx_platform_commit = 'opencraft-release/hawthorn.1'
