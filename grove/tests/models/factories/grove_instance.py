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
GroveInstance model - Factories
"""

# Imports #####################################################################

import factory
from factory.django import DjangoModelFactory

from grove.models.instance import GroveInstance


# Classes #####################################################################

class GroveInstanceFactory(DjangoModelFactory):
    """
    Factory for GroveInstance
    """
    class Meta:
        model = GroveInstance

    name = factory.Sequence('Test Grove Instance {}'.format)
