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
from unittest.mock import patch

import ddt
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from simple_email_confirmation.models import EmailAddress

from instance.models.appserver import Status
from instance.tests.base import create_user_and_profile
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from registration.models import BetaTestApplication


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
            "password": "Thisisapassword123()",
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
        import pdb; pdb.set_trace()
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
        ({"password": "INVALID"}),
        ({"password": "MissingSp3ci4lChars"}),
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
        response = self.client.patch(url, data={"password": "NewV4l1dPw()"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        # Should be able to log in with the new credentials
        self.assertTrue(self.client.login(username='test.user', password='NewV4l1dPw()'))


@ddt.ddt
class OpenEdXInstanceConfigAPITestCase(APITestCase):
    """
    Tests for the OpenEdXInstanceConfig APIs.
    """

    def setUp(self):
        self.user_with_instance = create_user_and_profile("instance.user", "instance.user@example.com")
        self.instance_config = BetaTestApplication.objects.create(
            user=self.user_with_instance,
            subdomain="somesubdomain",
            instance_name="User's Instance",
            public_contact_email="instance.user.public@example.com",
            privacy_policy_url="http://www.some/url"
        )
        EmailAddress.objects.create_confirmed(
            email=self.instance_config.public_contact_email,
            user=self.user_with_instance,
        )
        self.instance_config_defaults = dict(
            project_description="",
            privacy_policy_url="",
            use_advanced_theme=False,
            draft_theme_config=None,
        )
        self.user_without_instance = create_user_and_profile("noinstance.user", "noinstance.user@example.com")

    def _setup_user_instanace(self):
        """
        Set up an instance for the test user.
        """
        instance = OpenEdXInstanceFactory()
        self.instance_config.instance = instance
        self.instance_config.save()
        return instance

    def test_allow_public_validation(self):
        """
        Ensure that users can validate instance configuration without logging in.
        """
        response = self.client.post(reverse('api:v2:openedx-instance-config-validate'))
        self.assertNotEqual(response.status_code, 403)

    def test_create_new_instance_existing_error(self):
        """
        Test that a user that already has an instance cannot create a new one.

        This should hopefully be temporary if we support multiple instances per user.
        """
        self.client.force_login(self.user_with_instance)
        response = self.client.post(reverse('api:v2:openedx-instance-config-list'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json().get('user')[0],
            "User has reached limit of allowed Open edX instances.",
        )

    def test_create_new_instance_success(self):
        """
        Test successfully creating a new instance
        """
        self.client.force_login(self.user_without_instance)
        instance_data = dict(
            subdomain="newsubdomain",
            instance_name="My Instance",
            public_contact_email="noinstance.user.public@example.com",
        )
        response = self.client.post(
            reverse('api:v2:openedx-instance-config-list'),
            data=instance_data,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        # Checks that the instance data provided is a subset of the response.
        self.assertTrue(instance_data.items() <= response.json().items())
        # Make sure that the new public email is queued for verification
        self.assertTrue(
            EmailAddress.objects.filter(email="noinstance.user.public@example.com").exists()
        )

    @ddt.data(
        dict(subdomain="invalid subdomain"),
        dict(subdomain="invalid.subdomain"),
        dict(subdomain="invalid_subdomain"),
        dict(subdomain="invalid+subdomain"),
        dict(subdomain="somesubdomain"),  # Existing subdomain
        dict(instance_name=None),
        dict(instance_name=" "),
        dict(public_contact_email="invalid.email"),
        dict(public_contact_email=None),
        dict(draft_theme_config={}),
    )
    def test_instance_validation_failure(self, override):
        """
        Test validation issues when creating a new instance
        """
        self.client.force_login(self.user_without_instance)
        instance_data = dict(
            subdomain="newsubdomain",
            instance_name="My Instance",
            public_contact_email="noinstance.user.public@example.com",
        )
        instance_data.update(override)
        # Test validation with both the validate method and create method
        for view in ("list", "validate"):
            response = self.client.post(
                reverse(f"api:v2:openedx-instance-config-{view}"),
                data=instance_data,
                format="json",
            )
            self.assertEqual(response.status_code, 400)

    @ddt.data(
        ("instance.user", True),
        ("noinstance.user", False),
        (None, False),
    )
    @ddt.unpack
    def test_update_instance_permissions(self, username, has_permission):
        """
        Test that the owner of an instance has permission to update it, but others done.
        """
        if username is not None:
            self.client.force_login(User.objects.get(username=username))
        response = self.client.patch(reverse('api:v2:openedx-instance-config-detail', args=(self.instance_config.pk,)))
        if has_permission:
            self.assertNotIn(response.status_code, (403, 404))
        else:
            # An anonymous user should get 403 while an authenticated user should get 404
            self.assertIn(response.status_code, (403, 404))

    def test_commit_changes_fail_new_user(self):
        """
        Test that committing changes fails when a user is new.
        """
        self.client.force_login(self.user_with_instance)
        response = self.client.post(
            reverse('api:v2:openedx-instance-config-commit-changes', args=(self.instance_config.pk,))
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Must verify email", response.content.decode('utf-8'))

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_commit_changes_fail_running_appserver(self, mock_consul):
        """
        Test that committing changes fails when a user is new.
        """
        self.client.force_login(self.user_with_instance)
        instance = self._setup_user_instanace()
        make_test_appserver(instance, status=Status.ConfiguringServer)
        response = self.client.post(
            reverse('api:v2:openedx-instance-config-commit-changes', args=(self.instance_config.pk,))
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Instance launch already in progress", response.content.decode('utf-8'))

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    def test_commit_changes_email_validation_fail(self, mock_consul):
        """
        Test that committing changes fails when a user is new.
        """
        self._setup_user_instanace()
        EmailAddress.objects.get(
            email=self.instance_config.public_contact_email,
            user=self.user_with_instance,
        ).reset_confirmation()
        self.client.force_login(self.user_with_instance)
        url = reverse('api:v2:openedx-instance-config-commit-changes', args=(self.instance_config.pk,), )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Updated public email", response.content.decode('utf-8'))

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('registration.models.spawn_appserver')
    def test_commit_changes_success(self, mock_spawn_appserver, mock_consul):
        """
        Test that committing changes fails when a user is new.
        """
        self.client.force_login(self.user_with_instance)
        instance = self._setup_user_instanace()
        self.assertEqual(instance.privacy_policy_url, '')
        self.assertEqual(instance.email, 'contact@example.com')
        self.assertRegex(instance.name, r'Test Instance \d+')
        url = reverse('api:v2:openedx-instance-config-commit-changes', args=(self.instance_config.pk,), )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        mock_spawn_appserver.assert_called()
        instance.refresh_from_db()
        self.assertEqual(instance.privacy_policy_url, "http://www.some/url")
        self.assertEqual(instance.email, "instance.user.public@example.com")
        self.assertEqual(instance.name, "User's Instance")

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('registration.models.spawn_appserver')
    def test_commit_changes_force_running_appserver(self, mock_spawn_appserver, mock_consul):
        """
        Test that committing changes fails when a user is new.
        """
        self.client.force_login(self.user_with_instance)
        instance = self._setup_user_instanace()
        make_test_appserver(instance, status=Status.ConfiguringServer)
        url = reverse('api:v2:openedx-instance-config-commit-changes', args=(self.instance_config.pk,), )
        response = self.client.post(f"{url}?force=true")
        self.assertEqual(response.status_code, 200)
        mock_spawn_appserver.assert_called()
