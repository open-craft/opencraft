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
OpenEdXInstance model - Tests
"""

# Imports #####################################################################

import re

from instance.models.instance import OpenEdXInstance
from instance.tests.base import TestCase
from instance.tests.models.factories.instance import OpenEdXInstanceFactory


# Tests #######################################################################

class OpenEdXInstanceTestCase(TestCase):
    """
    Test cases for OpenEdXInstance models
    """
    # Factory boy doesn't properly support pylint+django
    #pylint: disable=no-member

    def test_new_instance(self):
        """
        New OpenEdXInstance object
        """
        self.assertFalse(OpenEdXInstance.objects.all())
        instance = OpenEdXInstanceFactory()
        self.assertEqual(OpenEdXInstance.objects.get().pk, instance.pk)
        self.assertTrue(re.search(r'Test Instance \d+ \(http://instance\d+.test.example.com/\)', str(instance)))
