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
Email verification view tests
"""

# Imports #####################################################################

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.core.urlresolvers import reverse

from simple_email_confirmation.models import EmailAddress


# Tests #######################################################################

class VerifyEmailTestCase(TestCase):
    """
    Tests for the verify_email view.
    """
    def setUp(self):
        self.user = User.objects.create(username='ThePurpleOne')
        self.email = EmailAddress.objects.create_unconfirmed(
            email='raspberryberet@example.com',
            user=self.user,
        )
        self.verification_url = reverse('email-verification:verify', kwargs={
            'code': self.email.key,
        })

    def test_verify_email(self):
        """
        Test that we can verify an email address.
        """
        response = self.client.get(self.verification_url)
        self.assertContains(response, 'Thank you for verifying your email address')
        self.email.refresh_from_db()
        self.assertIs(self.email.is_confirmed, True)

    @override_settings(SIMPLE_EMAIL_CONFIRMATION_PERIOD=timedelta(0))
    def test_verify_email_code_expired(self):
        """
        Test attempting to verify an email with an expired verification code.
        """
        response = self.client.get(self.verification_url)
        self.assertContains(response, 'Your email verification link has expired')
        self.email.refresh_from_db()
        self.assertIs(self.email.is_confirmed, False)

    def test_verify_unknown_code(self):
        """
        Check that attempting to verify an unknown code returns 404.
        """
        url = self.verification_url[:len(self.verification_url) - 5] + '/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
