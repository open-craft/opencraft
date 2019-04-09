# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <xavier@opencraft.com>
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
Tests for the registration models
"""

# Imports

from django.contrib.auth.models import User
from django.test import TestCase

from registration.models import BetaTestApplication


class BetaTestApplicationTestCase(TestCase):
    """
    Tests for beta test applications.
    """

    def test_update_existing_no_privacy_acceptance(self):
        """
        Ensure that we can update an existing application without it having
        accepted the privacy policy.
        """
        application = BetaTestApplication.objects.create(
            subdomain='test',
            instance_name='I did not accept',
            public_contact_email='test@example.com',
            accepted_privacy_policy=None,
            user=User.objects.create(username='test'),
        )
        application.something = 'something_else'
        application.save()
        application.refresh_from_db()
        self.assertIs(None, application.accepted_privacy_policy)
