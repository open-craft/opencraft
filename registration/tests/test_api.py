# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Tests for the registration API
"""

import ddt
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from simple_email_confirmation.models import EmailAddress

from instance.tests.base import create_user_and_profile


@ddt.ddt
class AccountAPITestCase(APITestCase):
    """
    Tests for the Account APIs.
    """

    def setUp(self):
        self.user = create_user_and_profile("test.user", "test.user@example.com")
        self.reference_time = timezone.now() - timezone.timedelta(hours=1)
        self.user.profile.accepted_privacy_policy = self.reference_time
        self.user.profile.save()
        self.user_data = {
            "username": "another.user",
            "password": "thisisapassword",
            "email": "another.user@some.domain",
        }
        self.profile_data = {
            "full_name": "Another User",
            "accepted_privacy_policy": self.reference_time,
            "accept_paid_support": True,
            "subscribe_to_updates": True
        }
        self.account_data = {**self.user_data, **self.profile_data}

    def test_allow_public_registration(self):
        """
        Ensure that users can register without needing to log in.
        """
        response = self.client.post(reverse('api:v2:accounts-list'))
        self.assertNotEqual(response.status_code, 403)

    @ddt.data(
        # Allow registration with or without subscribing to updates
        ({"subscribe_to_updates": True}),
        ({"subscribe_to_updates": False}),
    )
    def test_account_creation_success(self, override_data):
        """
        Test successfull registration with optionals.
        """
        data = self.account_data.copy()
        data.update(override_data)
        response = self.client.post(
            reverse("api:v2:accounts-list"),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        new_user_query = User.objects.filter(username=self.user_data.get('username'))
        self.assertTrue(new_user_query.exists())
        new_user = new_user_query.get()
        self.assertEqual(new_user.email, self.user_data.get('email'))
        self.assertEqual(new_user.username, self.user_data.get('username'))
        for field in self.profile_data:
            self.assertEqual(getattr(new_user.profile, field), data.get(field))
        # Ensure that the user's email is being verified
        self.assertTrue(EmailAddress.objects.filter(email=new_user.email).exists())

    @ddt.data(
        ({"full_name": None}),
        ({"username": None}),
        ({"username": "invalid username"}),
        ({"username": "invalid:"}),
        ({"email": None}),
        ({"email": "invalid.email"}),
        ({"password": None}),
        ({"password": "invalid"}),
        ({"password": "password123"}),
        ({"accepted_privacy_policy": None}),
        ({"accepted_privacy_policy": timezone.now() + timezone.timedelta(days=2)}),
        ({"accept_paid_support": False}),
    )
    def test_account_creation_failure_invalid(self, override_data):
        """
        Ensure that registration fails when invalid data is provided.
        """
        data = self.account_data.copy()
        data.update(override_data)
        response = self.client.post(
            reverse("api:v2:accounts-list"),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @ddt.data(
        ({"username": "test.user"}),
        ({"email": "test.user@example.com"}),
    )
    def test_account_creation_failure_existing(self, override_data):
        """
        Ensure that registration fails when username or email conflict with existing account.
        """
        data = self.account_data.copy()
        data.update(override_data)
        response = self.client.post(
            reverse("api:v2:accounts-list"),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @ddt.data("full_name", "username", "email", "password", "accepted_privacy_policy", "accept_paid_support")
    def test_account_creation_failure_missing(self, field_to_remove):
        """
        Ensure that registration fails when data is missing.
        """
        data = self.account_data.copy()
        data.pop(field_to_remove)
        response = self.client.post(
            reverse("api:v2:accounts-list"),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @ddt.data(
        ({"full_name": None}),
        ({"email": None}),
        ({"email": "invalid.email"}),
        ({"password": None}),
        ({"password": "invalid"}),
        ({"password": "password123"}),
        ({"accepted_privacy_policy": None}),
        ({"accepted_privacy_policy": timezone.now() + timezone.timedelta(hours=2)}),
        ({"accepted_privacy_policy": timezone.now() - timezone.timedelta(hours=1)}),
        ({"accept_paid_support": False}),
    )
    def test_account_update_failure(self, data):
        """
        Ensure that account data updates fail when new data is invalid.
        """
        self.client.force_login(self.user)
        response = self.client.patch(
            reverse("api:v2:accounts-detail", kwargs={'username': self.user.username}),
            data=data,
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @ddt.data(
        ('full_name', 'New Name'),
        ('subscribe_to_updates', True),
        ('subscribe_to_updates', False),
        ('accepted_privacy_policy', timezone.now()),
        # Accepts times that a little in the future to account for incorrect clocks
        ('accepted_privacy_policy', timezone.now() + timezone.timedelta(hours=1)),
    )
    @ddt.unpack
    def test_account_update_success(self, updated_field, new_value):
        """
        Test successful update of account data.
        """
        self.client.force_login(self.user)
        url = reverse("api:v2:accounts-detail", kwargs={'username': self.user.username})

        response = self.client.patch(url, data={updated_field: new_value}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.profile.refresh_from_db()
        self.assertEqual(getattr(self.user.profile, updated_field), new_value)

    def test_account_update_email_success(self):
        """
        Test successful update of user email and that it triggers email verification.
        """
        self.client.force_login(self.user)
        url = reverse("api:v2:accounts-detail", kwargs={'username': self.user.username})
        response = self.client.patch(url, data={"email": "new.email@example.com"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new.email@example.com")
        # If the user's email is updated, the updated email should also be verified
        self.assertTrue(EmailAddress.objects.filter(email="new.email@example.com").exists())

    def test_account_update_password_success(self):
        """
        Test password updates.
        """
        self.client.force_login(self.user)
        url = reverse("api:v2:accounts-detail", kwargs={'username': self.user.username})
        response = self.client.patch(url, data={"password": "newvalidpassword"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        # Should be able to log in with the new credentials
        self.assertTrue(self.client.login(username='test.user', password='newvalidpassword'))


@ddt.ddt
class OpenEdXInstanceConfigAPITestCase(APITestCase):
    """
    Tests for the OpenEdXInstanceConfig APIs.
    """
