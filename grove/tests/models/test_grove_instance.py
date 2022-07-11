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
GroveInstance model - Test
"""
import string

from django.conf import settings
from django.forms import ValidationError
from django.test import TestCase
from django.utils.crypto import get_random_string

from grove.models.instance import GroveInstance
from grove.tests.models.factories.grove_instance import GroveInstanceFactory


class TestGroveInstance(TestCase):
    """
    Test cases for Grove Instance
    """
    def test_grove_instance_name_limit(self):
        """
        Test name limit of Grove instance
        """
        grove_instance = GroveInstanceFactory(
            internal_lms_domain='sample.example.org',
            edx_platform_commit=settings.DEFAULT_OPENEDX_RELEASE
        )
        name_limit = settings.GROVE_INSTANCE_NAME_LENGTH_LIMIT

        name_exceeding_limit = get_random_string(length=name_limit + 1, allowed_chars=string.ascii_lowercase)
        # ValidationError is raised when exceeding limit
        with self.assertRaisesRegex(ValidationError, 'Grove instance name length must not exceed'):
            grove_instance.ref.name = name_exceeding_limit
            grove_instance.ref.clean()
            grove_instance.ref.save()

        # Save model successfully
        name_in_limit = get_random_string(length=name_limit - 1, allowed_chars=string.ascii_lowercase)
        grove_instance.ref.name = name_in_limit
        grove_instance.ref.clean()
        grove_instance.ref.save()
        db_instance = GroveInstance.objects.get(id=grove_instance.id)
        self.assertEqual(db_instance.ref.name, name_in_limit)
