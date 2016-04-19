# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
SingleVMOpenEdXInstance model - Factories
"""

# Imports #####################################################################
import uuid

import factory
from factory.django import DjangoModelFactory

from instance.models.instance import SingleVMOpenEdXInstance


# Classes #####################################################################

class SingleVMOpenEdXInstanceFactory(DjangoModelFactory):
    """
    Factory for SingleVMOpenEdXInstance
    """
    class Meta: #pylint: disable=missing-docstring
        model = SingleVMOpenEdXInstance

    sub_domain = factory.LazyAttribute(lambda o: '{}.integration'.format(str(uuid.uuid4())[:8]))
    name = factory.Sequence('Test Instance {}'.format)
    fork_name = 'edx/edx-platform'
    ref_type = 'tags'
    branch_name = 'named-release/cypress' # Use a known working version
    ansible_source_repo_url = 'https://github.com/open-craft/configuration.git'
    configuration_version = 'integration'
    ansible_playbook_name = 'opencraft_integration'
    forum_version = 'named-release/cypress'
    notifier_version = 'named-release/cypress'
    xqueue_version = 'named-release/cypress'
    certs_version = 'named-release/cypress'
    use_ephemeral_databases = True
