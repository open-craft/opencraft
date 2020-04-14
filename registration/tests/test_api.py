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
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from simple_email_confirmation.models import EmailAddress
from instance.models.appserver import Status
from instance.schemas.theming import DEFAULT_THEME
from instance.tests.base import create_user_and_profile
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from registration.models import BetaTestApplication

from .utils import create_image


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

    def _setup_user_instance(self):
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

    @patch('random.choices', return_value=['1', '2', '3', '4', '5'])
    def test_create_new_instance_success_external_domain(self, mock_random):
        """
        Test successfully creating a new instance with an external domain
        """
        self.client.force_login(self.user_without_instance)
        instance_data = dict(
            external_domain="newsubdomain.com",
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
        # Checks that autogenerated slug is correct
        self.assertEqual(response.json()['subdomain'], 'newsubdomaincom-12345')
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
        dict(external_domain="invalid external domain"),
        dict(instance_name=None),
        dict(instance_name=" "),
        dict(public_contact_email="invalid.email"),
        dict(public_contact_email=None),
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

    def test_theme_config_api_no_theme_set(self):
        """
        Test updating theming values
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        response = self.client.patch(
            reverse(f"api:v2:openedx-instance-config-theme-config", args=(self.instance_config.pk,)),
            data={
                "version": 1
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @ddt.data(
        {"main-color": "#ffaaff"},
        {"main-color": "#ffaaff", "link-color": "#aabbaa"},
        {"main-color": "#ffaaff", "link-color": "#aabbaa", "footer-color": "#123542"},
    )
    def test_theme_config_api_change_theme(self, theme_data):
        """
        Test updating theming values
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        # Set up simple theme
        self.instance_config.draft_theme_config = DEFAULT_THEME
        self.instance_config.save()

        # Request changes
        response = self.client.patch(
            reverse(f"api:v2:openedx-instance-config-theme-config", args=(self.instance_config.pk,)),
            data=theme_data,
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Check if changes were saved
        self.instance_config.refresh_from_db()
        for key, value in theme_data.items():
            self.assertEqual(self.instance_config.draft_theme_config[key], value)

    def test_theme_config_api_erase_value(self):
        """
        Test updating theming values
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        # Set up simple theme
        self.instance_config.draft_theme_config = {**DEFAULT_THEME}  # Copy dict instead of assgning it
        self.instance_config.draft_theme_config['main-nav-color'] = "#fafafa"
        self.instance_config.save()

        response = self.client.patch(
            reverse(f"api:v2:openedx-instance-config-theme-config", args=(self.instance_config.pk,)),
            data={
                "main-color": "",
                "main-nav-color": ""
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Check if changes were saved
        self.instance_config.refresh_from_db()
        # Empty fields sent through the API should have either the default
        # simple theme value for required values or an undefined key
        self.assertEqual(
            DEFAULT_THEME["main-color"],
            self.instance_config.draft_theme_config["main-color"]
        )
        self.assertNotIn("btn-sign-in-bg", self.instance_config.draft_theme_config.keys())

    def test_theme_config_api_update_flag(self):
        """
        Test updating theming flags.
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        # Set up simple theme.
        self.instance_config.draft_theme_config = {**DEFAULT_THEME}  # Copy dict instead of assigning it.
        self.instance_config.draft_theme_config.update({
            "btn-sign-in-bg": "#fafafa",
            "btn-sign-in-color": "#fafafa",
            "btn-sign-in-border-color": "#fafafa",
            "btn-sign-in-hover-bg": "#fafafa",
            "btn-sign-in-hover-color": "#fafafa",
        })
        self.instance_config.save()

        # Check that it's not possible to enable button customization with "hover border color" missing.
        response = self.client.patch(
            reverse(f"api:v2:openedx-instance-config-theme-config", args=(self.instance_config.pk,)),
            data={
                "customize-sign-in-btn": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"non_field_errors": "Schema validation failed."})

        # Add missing property and enable customization.
        response = self.client.patch(
            reverse(f"api:v2:openedx-instance-config-theme-config", args=(self.instance_config.pk,)),
            data={
                "btn-sign-in-hover-border-color": "#fafafa",
                "customize-sign-in-btn": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Check if changes were saved.
        self.instance_config.refresh_from_db()
        self.assertTrue(self.instance_config.draft_theme_config["customize-sign-in-btn"])

        # Disable customization.
        response = self.client.patch(
            reverse(f"api:v2:openedx-instance-config-theme-config", args=(self.instance_config.pk,)),
            data={
                "customize-sign-in-btn": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Check if changes were saved.
        self.instance_config.refresh_from_db()
        # Disabled customization (flag) should not exist in the theme.
        self.assertIsNone(self.instance_config.draft_theme_config.get("customize-sign-in-btn"))

    def test_change_logo(self):
        """
        Test uploading logo
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        # Load test logo image
        logo = create_image('logo.png')
        logo_file = SimpleUploadedFile('logo.png', logo.getvalue())

        # Request
        response = self.client.post(
            reverse(f"api:v2:openedx-instance-config-image", args=(self.instance_config.pk,)),
            data={'logo': logo_file},
            format='multipart',
        )
        self.assertEqual(response.status_code, 200)

    def test_set_hero_cover_image(self):
        """
        Test uploading a hero cover image
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()
        self.assertFalse(self.instance_config.hero_cover_image)

        # Load test cover image
        cover_image = create_image('cover.png')
        cover_image_file = SimpleUploadedFile('cover.png', cover_image.getvalue())

        # Request
        response = self.client.post(
            reverse(f"api:v2:openedx-instance-config-image", args=(self.instance_config.pk,)),
            data={'hero_cover_image': cover_image_file},
            format='multipart',
        )
        self.assertTrue(response.status_code, 200)
        self.instance_config.refresh_from_db()
        self.assertTrue(self.instance_config.hero_cover_image)

    def test_delete_hero_cover_image(self):
        """
        Test deleting the already set hero cover image
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()
        self.assertFalse(self.instance_config.hero_cover_image)

        # Load test cover image
        cover_image = create_image('cover.png')
        cover_image_file = SimpleUploadedFile('cover2.png', cover_image.getvalue())

        # Request
        response = self.client.post(
            reverse(f"api:v2:openedx-instance-config-image", args=(self.instance_config.pk,)),
            data={'hero_cover_image': cover_image_file},
            format='multipart',
        )
        self.assertTrue(response.status_code, 200)
        self.instance_config.refresh_from_db()
        self.assertTrue(self.instance_config.hero_cover_image)

        # Deletion request
        response = self.client.post(
            reverse(f"api:v2:openedx-instance-config-image", args=(self.instance_config.pk,)),
            data={'hero_cover_image': ''},
            format='multipart',
        )
        self.assertEqual(response.status_code, 200)
        self.instance_config.refresh_from_db()
        self.assertFalse(self.instance_config.hero_cover_image)

    def test_change_logo_wrong_size(self):
        """
        Test uploading logo with wrong size
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        # Load test logo image
        logo = create_image('logo.png', size=(100, 100))
        logo_file = SimpleUploadedFile('logo.png', logo.getvalue())

        # Request
        response = self.client.post(
            reverse(f"api:v2:openedx-instance-config-image", args=(self.instance_config.pk,)),
            data={'logo': logo_file},
            format='multipart',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {
                'logo': ['The logo image must be 48px tall to fit into the header.']
            }
        )

    def test_change_favicon(self):
        """
        Test uploading favicon
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        # Load test logo image
        logo = create_image('logo.ico', size=(10, 10))
        logo_file = SimpleUploadedFile('logo.ico', logo.getvalue())

        # Request
        response = self.client.post(
            reverse(f"api:v2:openedx-instance-config-image", args=(self.instance_config.pk,)),
            data={'favicon': logo_file},
            format='multipart',
        )
        self.assertEqual(response.status_code, 200)

    def test_static_content_overrides_config_when_no_existing_config(self):
        """
        Test updating the static content overrides configuration when there is no existing configuration.
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        response = self.client.patch(
            reverse(
                f"api:v2:openedx-instance-config-static-content-overrides",
                args=(self.instance_config.pk, )
            ),
            data={'static_template_about_content': 'Hello world!'},
            format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.instance_config.refresh_from_db()
        expected_values = {
            'version': 0,
            'static_template_about_content': 'Hello world!',
            'homepage_overlay_html': '<h1>Welcome to {}</h1><p>It works! Powered by Open edX®</p>'.format(
                self.instance_config.instance_name
            )
        }
        self.assertEqual(self.instance_config.draft_static_content_overrides, expected_values)

    @ddt.data(
        {'static_template_about_header': 'About Page'},
        {'static_template_about_content': 'Hello world!'},
        {'static_template_about_header': 'About Us', 'static_template_about_content': 'Hello World!'}
    )
    def test_patch_static_content_overrides_config(self, static_content_overrides_data):
        """
        Test updating the static content overrides configuration.
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        self.instance_config.draft_static_content_overrides = {
            'version': 0, 'static_template_contact_content': 'Email: contact@example.com'
        }
        self.instance_config.save()

        response = self.client.patch(
            reverse(
                f"api:v2:openedx-instance-config-static-content-overrides",
                args=(self.instance_config.pk, )
            ),
            data=static_content_overrides_data,
            format='json'
        )
        self.assertEqual(response.status_code, 200)

        self.instance_config.refresh_from_db()
        for key, value in static_content_overrides_data.items():
            self.assertEqual(self.instance_config.draft_static_content_overrides[key], value)

    def test_check_config_urls(self):
        """
        Test if the LMS and Studio url variables behave correctly
        """
        self.client.force_login(self.user_with_instance)
        self._setup_user_instance()

        response = self.client.get(reverse(f"api:v2:openedx-instance-config-list"))

        # Retrieve instance data and check that instance urls are present and not empty
        instance_data = dict(response.data[0])

        self.assertIn('lms_url', instance_data.keys())
        self.assertIn('studio_url', instance_data.keys())
        self.assertIsNot(instance_data.get('lms_url'), "")
        self.assertIsNot(instance_data.get('studio_url'), "")

        # Detach instance from application and check that urls are empty
        self.instance_config.instance = None
        self.instance_config.save()

        response = self.client.get(reverse(f"api:v2:openedx-instance-config-list"))

        # Retrieve instance data and check that instance urls are present and empty
        instance_data = dict(response.data[0])

        self.assertIn('lms_url', instance_data.keys())
        self.assertIn('studio_url', instance_data.keys())
        self.assertEqual(instance_data.get('lms_url'), "")
        self.assertEqual(instance_data.get('studio_url'), "")


@ddt.ddt
class InstanceDeploymentAPITestCase(APITestCase):
    """
    Tests for the OpenEdXInstanceDeployment APIs.
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

    def _setup_user_instance(self):
        """
        Set up an instance for the test user.
        """
        instance = OpenEdXInstanceFactory()
        self.instance_config.instance = instance
        self.instance_config.save()
        return instance

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('registration.models.spawn_appserver')
    def test_get_deployment_status_no_active(self, mock_spawn_appserver, mock_consul):
        """
        Test that the correct status is returned when provisioning first instance.
        """
        self.client.force_login(self.user_with_instance)
        instance = self._setup_user_instance()
        make_test_appserver(instance, status=Status.ConfiguringServer)

        url = reverse('api:v2:openedx-instance-deployment-detail', args=(self.instance_config.pk,), )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'PREPARING_INSTANCE', 'undeployed_changes': 0})

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('registration.models.spawn_appserver')
    def test_get_deployment_status_up_to_date(self, mock_spawn_appserver, mock_consul):
        """
        Test that the correct status is returned when instance is up-to-date.
        """
        self.client.force_login(self.user_with_instance)
        instance = self._setup_user_instance()
        instance.name = self.instance_config.instance_name
        instance.privacy_policy_url = self.instance_config.privacy_policy_url
        instance.email = self.instance_config.public_contact_email
        instance.theme_config = self.instance_config.draft_theme_config
        instance.save()

        app_server = make_test_appserver(instance, status=Status.Running)
        app_server.is_active = True  # Outside of tests, use app_server.make_active() instead
        app_server.save()

        url = reverse('api:v2:openedx-instance-deployment-detail', args=(self.instance_config.pk,), )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'UP_TO_DATE', 'undeployed_changes': 0})

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('registration.models.spawn_appserver')
    def test_get_deployment_status_pending_changes(self, mock_spawn_appserver, mock_consul):
        """
        Test that the correct status is returned when there's changes to be deployed.
        """
        self.client.force_login(self.user_with_instance)
        instance = self._setup_user_instance()
        app_server = make_test_appserver(instance, status=Status.Running)
        app_server.is_active = True  # Outside of tests, use app_server.make_active() instead
        app_server.save()

        url = reverse('api:v2:openedx-instance-deployment-detail', args=(self.instance_config.pk,), )
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'PENDING_CHANGES', 'undeployed_changes': 3})

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('registration.models.spawn_appserver')
    def test_get_deployment_status_preparing_instance(self, mock_spawn_appserver, mock_consul):
        """
        Test that the correct status is returned when provisioning first instance.
        """
        self.client.force_login(self.user_with_instance)

        url = reverse('api:v2:openedx-instance-deployment-detail', args=(self.instance_config.pk,), )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'status': 'PREPARING_INSTANCE', 'undeployed_changes': 0})

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('registration.models.spawn_appserver')
    def test_cancel_first_deployment_fails(self, mock_spawn_appserver, mock_consul):
        """
        Test that trying to stop the first provisioning fails.
        """
        self.client.force_login(self.user_with_instance)
        instance = self._setup_user_instance()
        make_test_appserver(instance, status=Status.ConfiguringServer)

        url = reverse('api:v2:openedx-instance-deployment-detail', args=(self.instance_config.pk,), )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 400)

    @patch(
        'instance.tests.models.factories.openedx_instance.OpenEdXInstance._write_metadata_to_consul',
        return_value=(1, True)
    )
    @patch('registration.models.spawn_appserver')
    def test_cancel_deployment(self, mock_spawn_appserver, mock_consul):
        """
        Test that trying to stop a provisioning succeeds.
        """
        self.client.force_login(self.user_with_instance)
        instance = self._setup_user_instance()
        app_server = make_test_appserver(instance, status=Status.Running)
        app_server.is_active = True  # Outside of tests, use app_server.make_active() instead
        app_server.save()
        make_test_appserver(instance, status=Status.ConfiguringServer)

        url = reverse('api:v2:openedx-instance-deployment-detail', args=(self.instance_config.pk,), )
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)

    def test_commit_changes_fail_new_user(self):
        """
        Test that committing changes fails when a user is new.
        """
        self.client.force_login(self.user_with_instance)
        response = self.client.post(
            reverse('api:v2:openedx-instance-deployment-list'),
            data={"id": self.instance_config.id}
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
        instance = self._setup_user_instance()
        make_test_appserver(instance, status=Status.ConfiguringServer)
        response = self.client.post(
            reverse('api:v2:openedx-instance-deployment-list'),
            data={"id": self.instance_config.id}
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
        self._setup_user_instance()
        EmailAddress.objects.get(
            email=self.instance_config.public_contact_email,
            user=self.user_with_instance,
        ).reset_confirmation()
        self.client.force_login(self.user_with_instance)
        response = self.client.post(
            reverse('api:v2:openedx-instance-deployment-list'),
            data={"id": self.instance_config.id}
        )
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
        instance = self._setup_user_instance()
        self.assertEqual(instance.privacy_policy_url, '')
        self.assertEqual(instance.email, 'contact@example.com')
        self.assertRegex(instance.name, r'Test Instance \d+')
        response = self.client.post(
            reverse('api:v2:openedx-instance-deployment-list'),
            data={"id": self.instance_config.id}
        )
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
        instance = self._setup_user_instance()
        make_test_appserver(instance, status=Status.ConfiguringServer)
        url = reverse('api:v2:openedx-instance-deployment-list')
        response = self.client.post(f"{url}?force=true", data={"id": self.instance_config.id})
        self.assertEqual(response.status_code, 200)
        mock_spawn_appserver.assert_called()
