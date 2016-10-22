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
LoadBalancingServer model - tests
"""

from django.conf import settings

from instance.tests.base import TestCase
from instance.tests.models.factories.load_balancer import LoadBalancingServerFactory


class LoadBalancingServerTest(TestCase):
    """
    Test cases for the LoadBalancingServer model.
    """

    def test_get_fragment_name(self):
        """Test fragment name generation is sane."""
        load_balancer = LoadBalancingServerFactory()
        fragment_name = load_balancer.get_fragment_name()
        self.assertEqual(
            fragment_name,
            settings.LOAD_BALANCER_FRAGMENT_NAME_PREFIX + load_balancer.fragment_name_postfix
        )
        self.assertEqual(fragment_name, load_balancer.get_fragment_name())
