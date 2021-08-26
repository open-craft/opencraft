# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <xavier@opencraft.com>
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
Tests for the marketing views
"""

# Imports #####################################################################

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from registration.models import BetaTestApplication
from userprofile.models import UserProfile

# Tests #######################################################################

class ConversionViewTestCase(TestCase):
    """
    Test case for the conversion view.
    """
    def setUp(self):
        """
        Set up the properties needed for the tests.
        """
        self.client = Client()

    def _get_user(self, is_superuser=False):
        """
        Create and return a user of the specified type.
        """
        user, _ = User.objects.get_or_create(username='test', email='test@example.com')
        user.set_password('test')
        if is_superuser:
            user.is_superuser = True
        user.save()
        return user

    def _login_as_user(self, is_superuser=False):
        """
        Log in as a super user.
        """
        user = self._get_user(is_superuser)
        self.client.login(username=user.username, password='test')

    def test_login_required(self):
        """
        Test that a user has to be logged in to access the marketing conversion page.
        """
        response = self.client.get(reverse('marketing:conversion'))
        expected_redirect_url = '/login/?next={}'.format(reverse('marketing:conversion'))
        self.assertRedirects(response, expected_redirect_url, fetch_redirect_response=False)

    def test_super_user_required(self):
        """
        Test that the user has to be logged in to an account with superuser permissions to
        access the marketing conversion page.
        """
        self._login_as_user()
        response = self.client.get(reverse('marketing:conversion'))
        expected_redirect_url = '/login/?next={}'.format(reverse('marketing:conversion'))
        self.assertRedirects(response, expected_redirect_url, fetch_redirect_response=False)

    def test_page_loads_for_a_super_user(self):
        """
        Test that the page loads for a superuser.
        """
        self._login_as_user(is_superuser=True)
        response = self.client.get(reverse('marketing:conversion'))

        self.assertEqual(response.status_code, 200)

    def test_page_has_an_unbound_form_with_all_expected_fields(self):
        """
        Test that the page has an unbound form with all the expected fields.
        """
        self._login_as_user(is_superuser=True)
        response = self.client.get(reverse('marketing:conversion'))
        self.assertIn('form', response.context)
        self.assertFalse(response.context['form'].is_bound)
        self.assertIn('instance', response.context['form'].fields)
        self.assertIn('revenue', response.context['form'].fields)
        self.assertIn('custom_matomo_tracking_data', response.context['form'].fields)

    def test_required_fields(self):
        """
        Test that the missing required fields returns an error.
        """
        self._login_as_user(is_superuser=True)
        # Note: we need to send an empty value for 'custom_matomo_tracking_data' since otherwise the bound
        # value of the corresponding JSONField will be None and Django form will error out when
        # trying to deserialize that.
        response = self.client.post(reverse('marketing:conversion'), data={'custom_matomo_tracking_data': ''})

        self.assertTrue(len(response.context['form'].errors) > 0)
        expected_errors = {'instance': ['This field is required.'], 'revenue': ['This field is required.']}
        self.assertEqual(response.context['form'].errors, expected_errors)

    def test_instance_id_not_in_queryset(self):
        """
        Test that an error is returned when the instance ID submitted in the POST request is not
        in the queryset for the field.
        """
        self._login_as_user(is_superuser=True)

        response = self.client.post(
            reverse('marketing:conversion'),
            data={
                'instance': '1',
                'revenue': '10.00',
                'custom_matomo_tracking_data': '',
            }
        )
        self.assertEqual(
            response.context['form'].errors,
            {'instance': ['Select a valid choice. That choice is not one of the available choices.']}
        )

    def test_custom_matomo_tracking_data_invalid_json(self):
        """
        Test that a validation error is raised when invalid JSON is sent for the
        'custom_matomo_tracking_data' field.
        """
        user = self._get_user(is_superuser=True)

        UserProfile.objects.create(
            user=user,
            full_name='test name',
            accepted_privacy_policy="2021-01-01 00:00:00+0000"
        )
        application = BetaTestApplication.objects.create(
            user=user,
            subdomain='test',
            instance_name='Test instance',
            project_description='Test instance creation.',
            public_contact_email=user.email,
        )
        application.instance = OpenEdXInstanceFactory()
        application.save()
        application.instance.successfully_provisioned = True
        application.instance.save()

        self._login_as_user(is_superuser=True)

        response = self.client.post(
            reverse('marketing:conversion'),
            data={
                'instance': str(application.instance.id),
                'revenue': '10.00',
                'custom_matomo_tracking_data': 'This is a sentence.'
            }
        )
        self.assertEqual(
            response.context['form'].errors,
            {'custom_matomo_tracking_data': ['The value must be valid JSON.']}
        )
