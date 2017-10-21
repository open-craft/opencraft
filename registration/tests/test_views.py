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
Tests for the registration views
"""

# Imports #####################################################################

from collections import defaultdict
import json
import re
from unittest.mock import patch

from bs4 import BeautifulSoup
from ddt import ddt, data, unpack
from django.core import mail
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from simple_email_confirmation.models import EmailAddress

from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from registration.forms import BetaTestApplicationForm
from registration.models import BetaTestApplication
from registration.tests.utils import UserMixin


# Tests #######################################################################

@ddt
class BetaTestApplicationViewTestMixin:
    """
    Tests for beta test applications.
    """
    maxDiff = None

    def setUp(self): #pylint: disable=invalid-name
        """
        Initialize the test case with some valid data.
        """
        super().setUp()
        self.form_data = {
            'subdomain': 'hogwarts',
            'instance_name': 'Hogwarts',
            'full_name': 'Albus Dumbledore',
            'username': 'albus',
            'email': 'albus.dumbledore@hogwarts.edu',
            'public_contact_email': 'support@hogwarts.edu',
            'password': 'gryffindor',
            'password_strength': 3,
            'password_confirmation': 'gryffindor',
            'project_description': 'Online courses in Witchcraft and Wizardry',
            'accept_terms': True,
            'subscribe_to_updates': False,
            'main_color': '#001122',
            'link_color': '#001122',
            'header_bg_color': '#ffffff',
            'footer_bg_color': '#ffffff',
        }

    def _assert_registration_succeeds(self, form_data):
        """
        Assert that the given application form data creates new user, profile
        and registration instances, sends email verification messages, and
        displays a success message.
        """
        # Fill in the form and submit the registration
        response = self._register(form_data)
        self._assert_success_response(response)

        # Check that the application matches the submitted data
        application = BetaTestApplication.objects.get()
        self._assert_application_matches_form_data(application)

        # Test the email verification flow
        self._assert_email_verification_sent(application)
        with patch('registration.provision._provision_instance', autospec=True) as mock_handler:
            expected_call_count = 0
            for verification_email in mail.outbox:
                verify_url = re.search(r'https?://[^\s]+',
                                       verification_email.body).group(0)
                self.client.get(verify_url)
                expected_call_count += 1
            # Check to make sure we called _provision_instance when emails were verified.
            self.assertEqual(mock_handler.call_count, expected_call_count)
        self._assert_email_addresses_verified(application)

    def _assert_success_response(self, response):
        """
        Assert that a success message is displayed and that the form fields
        display the correct data for the registered user.
        """
        response_body = re.sub(r'\s+', ' ', response)
        self.assertIn('Thank you for applying for the OpenCraft beta',
                      response_body)
        self.assertIn('pending email confirmation', response_body)
        form_fields = {name: field
                       for name, field in self._get_form_fields(response).items()
                       if name not in {'password',
                                       'password_strength',
                                       'password_confirmation',
                                       'csrfmiddlewaretoken',
                                       'main_color',
                                       'link_color',
                                       'header_bg_color',
                                       'footer_bg_color',
                                       'logo',
                                       'favicon'}}
        form_values = {name: field['value']
                       for name, field in form_fields.items()}
        expected_values = {name: value
                           for name, value in self.form_data.items()
                           if name not in {'password',
                                           'password_strength',
                                           'password_confirmation',
                                           'main_color',
                                           'link_color',
                                           'header_bg_color',
                                           'footer_bg_color',
                                           'logo',
                                           'favicon'}}
        self.assertEqual(form_values, expected_values)
        for name, field in form_fields.items():
            if field.get('type') != 'checkbox':
                if name in BetaTestApplicationForm.can_be_modified:
                    self.assertNotIn(
                        'readonly', field,
                        '{0} should not be read only'.format(name)
                    )
                else:
                    self.assertIn(
                        'readonly', field,
                        '{0} should be read only'.format(name)
                    )

    def _assert_application_matches_form_data(self, application):
        """
        Assert that the application instance matches the form data.
        """
        for application_field in ('subdomain',
                                  'instance_name',
                                  'public_contact_email',
                                  'project_description'):
            self.assertEqual(getattr(application, application_field),
                             self.form_data[application_field])
        self.assertEqual(application.subscribe_to_updates,
                         bool(self.form_data.get('subscribe_to_updates')))
        self._assert_user_matches_form_data(application.user)
        self._assert_profile_matches_form_data(application.user.profile)

    def _assert_user_matches_form_data(self, user):
        """
        Assert that the registered user matches the form data.
        """
        for user_field in ('username', 'email'):
            self.assertEqual(getattr(user, user_field),
                             self.form_data[user_field])
        self.assertTrue(user.check_password(self.form_data['password']))

    def _assert_profile_matches_form_data(self, profile):
        """
        Assert that the registered user's profile matches the form data.
        """
        self.assertEqual(profile.full_name, self.form_data['full_name'])

    def _assert_email_verification_sent(self, application):
        """
        Assert that verification emails were sent to the email addresses given
        on the beta application.
        """
        addresses = {application.user.email, application.public_contact_email}
        self.assertEqual(len(mail.outbox), len(addresses))
        self.assertEqual(EmailAddress.objects.count(), len(addresses))
        for email_address in addresses:
            email = EmailAddress.objects.get(email=email_address)
            self.assertIs(email.is_confirmed, False)

    def _assert_email_addresses_verified(self, application):
        """
        Assert that the email addresses given on the beta application have
        been verified.
        """
        for email_address in {application.user.email,
                              application.public_contact_email}:
            email = EmailAddress.objects.get(email=email_address)
            self.assertIs(email.is_confirmed, True)
        response = self._get_response_body(self.url)
        self.assertNotIn('pending email confirmation',
                         re.sub(r'\s+', ' ', response))

    def _assert_registration_fails(self, form_data, expected_errors=None):
        """
        Assert that the given application form data does not create new user,
        profile and registration instances, or send email verification
        messages.
        """
        original_count = BetaTestApplication.objects.count()
        response = self._register(form_data)
        if expected_errors:
            self.assertEqual(self._get_error_messages(response),
                             expected_errors)
        self.assertEqual(BetaTestApplication.objects.count(), original_count)
        self.assertEqual(len(mail.outbox), 0)

    def test_valid_application(self):
        """
        Test a valid beta test application.
        """
        self._assert_registration_succeeds(self.form_data)

    def test_invalid_subdomain(self):
        """
        Invalid characters in the subdomain.
        """
        self.form_data['subdomain'] = 'hogwarts?'
        self._assert_registration_fails(self.form_data, expected_errors={
            'subdomain': ["Please include only letters, numbers, '_', '-' "
                          "and '.'"],
        })

    def test_existing_subdomain(self):
        """
        Subdomain already taken.
        """
        BetaTestApplication.objects.create(
            subdomain=self.form_data['subdomain'],
            instance_name='I got here first',
            public_contact_email='test@example.com',
            project_description='test',
            user=User.objects.create(username='test'),
        )
        self._assert_registration_fails(self.form_data, expected_errors={
            'subdomain': ['This domain is already taken.'],
        })

    @override_settings(SUBDOMAIN_BLACKLIST=['www'])
    def test_blacklisted_subdomain(self):
        """
        Blacklisted subdomains should be rejected.
        """
        self.form_data['subdomain'] = 'www'
        self._assert_registration_fails(self.form_data, expected_errors={
            'subdomain': ['This domain name is not publicly available.'],
        })

    def test_instance_subdomain(self):
        """
        Subdomain used by an existing instance.
        """
        OpenEdXInstanceFactory.create(
            sub_domain=self.form_data['subdomain'],
        )
        self._assert_registration_fails(self.form_data, expected_errors={
            'subdomain': ['This domain is already taken.'],
        })

    def test_subdomain_with_base_domain(self):
        """
        Subdomain that includes the base domain.
        """
        form_data = self.form_data.copy()
        form_data['subdomain'] += '.' + BetaTestApplication.BASE_DOMAIN
        self._assert_registration_succeeds(form_data)

    def test_invalid_username(self):
        """
        Invalid characters in the username.
        """
        self.form_data['username'] = 'albus@dumbledore'
        self._assert_registration_fails(self.form_data, expected_errors={
            'username': ['Usernames may contain only letters, numbers, and '
                         './+/-/_ characters.'],
        })

    def test_existing_username(self):
        """
        Username already taken.
        """
        BetaTestApplication.objects.create(
            subdomain='test',
            instance_name='That username is mine',
            public_contact_email='test@example.com',
            project_description='test',
            user=User.objects.create(username=self.form_data['username']),
        )
        self._assert_registration_fails(self.form_data, expected_errors={
            'username': ['This username is already taken.'],
        })

    def test_invalid_email(self):
        """
        Invalid email address.
        """
        self.form_data['email'] = 'albus'
        self._assert_registration_fails(self.form_data, expected_errors={
            'email': ['Enter a valid email address.'],
        })

    def test_existing_email(self):
        """
        Email address already taken.
        """
        BetaTestApplication.objects.create(
            subdomain='test',
            instance_name='That email address is mine',
            public_contact_email='test@example.com',
            project_description='test',
            user=User.objects.create(username='test', email=self.form_data['email']),
        )
        self._assert_registration_fails(self.form_data, expected_errors={
            'email': ['This email address is already registered.'],
        })

    def test_invalid_public_contact_email(self):
        """
        Invalid public contact email address.
        """
        self.form_data['public_contact_email'] = 'hogwarts'
        self._assert_registration_fails(self.form_data, expected_errors={
            'public_contact_email': ['Enter a valid email address.'],
        })

    @data(
        ('password', 0),
        ('querty', 0),
        ('Hogwarts', 1),
    )
    @unpack
    def test_weak_password(self, password, password_strength):
        """
        Password not strong enough.
        """
        self.form_data['password'] = password
        self.form_data['password_confirmation'] = password
        self.form_data['password_strength'] = password_strength
        self._assert_registration_fails(self.form_data, expected_errors={
            'password': ['Please use a stronger password: avoid common '
                         'patterns and make it long enough to be '
                         'difficult to crack.'],
        })

    def test_password_mismatch(self):
        """
        Password confirmation does not match password.
        """
        self.form_data['password_confirmation'] = 'slytherin'
        self._assert_registration_fails(self.form_data, expected_errors={
            'password_confirmation': ["The two password fields didn't match."],
        })

    @override_settings(VARIABLES_NOTIFICATION_EMAIL=None)
    def test_existing_user(self):
        """
        Logged in user already exists but has not registered.
        """
        User.objects.create_user(
            username=self.form_data['username'],
            email=self.form_data['email'],
            password=self.form_data['password'],
        )
        self._login(username=self.form_data['username'],
                    password=self.form_data['password'])

        # The password fields do not appear on the form for logged in users
        form_data = self.form_data.copy()
        del form_data['password']
        del form_data['password_strength']
        del form_data['password_confirmation']
        self._assert_registration_succeeds(form_data)

    def _get_response_body(self, url):
        """
        Navigate to the given url and return the response body as a string.
        Override this method when testing using something other than the
        django test client (e.g. selenium).
        """
        response = self.client.get(url, follow=True)
        return response.content.decode('utf-8')

    def _register(self, form_data):
        """
        Register with the given application form data, and return the response
        content as a string. Override this method when testing using
        something other than the django test client (e.g. selenium).
        """
        getter = getattr(self.client, self.request_method)
        response = getter(self.url, form_data, follow=True)
        return response.content.decode('utf-8')

    def _login(self, **kwargs):
        """
        Log in with the given credentials. Override this method when testing using
        something other than the django test client (e.g. selenium).
        """
        self.client.login(**kwargs)

    @staticmethod
    def _get_form_fields(response):
        """
        Extract the form fields from the response. Returns a dict mapping
        field names to dicts with a `value` key set to the field value, and
        other attributes corresponding to the html element attributes.
        """
        soup = BeautifulSoup(response, 'html.parser')
        form = soup.find(attrs={'id': 'registration-form'})
        controls = form.find_all(attrs={'name': bool})
        fields = {}
        for el in controls:
            name = el['name']
            attrs = el.attrs
            if el.name == 'textarea':
                attrs['value'] = el.text.strip()
            elif el['type'] == 'checkbox':
                attrs['value'] = bool(el.get('checked'))
            fields[name] = attrs
        return fields

    @staticmethod
    def _get_error_messages(response):
        """
        Extract the error messages from the response.
        """
        soup = BeautifulSoup(response, 'html.parser')
        attrs = {'class': 'djng-field-errors'}
        error_lists = [ul for ul in soup.find_all('ul', attrs=attrs)
                       if ul['ng-show'].endswith('$pristine')]
        errors = defaultdict(list)
        for error_list in error_lists:
            pattern = r"(?:form\.(\w+)|form\['(\w+)'\])"
            match = re.match(pattern, error_list['ng-show'])
            name = next(group for group in match.groups() if group)
            for error in error_list.find_all('li'):
                if error.text:
                    errors[name].append(error.text)
        return errors


class BetaTestApplicationViewTestCase(BetaTestApplicationViewTestMixin,
                                      TestCase):
    """
    Tests for beta test applications.
    """
    url = reverse('registration:register')
    request_method = 'post'

    def test_modify_immutable_fields(self):
        """
        Check that non-modifiable fields cannot be modified once a user has
        registered.
        """
        self._register(self.form_data)
        modified = self.form_data.copy()
        modified.update({
            'instance_name': 'Azkaban',
            'username': 'snape',
        })
        self._register(modified)
        application = BetaTestApplication.objects.get()
        self._assert_application_matches_form_data(application)

    @override_settings(VARIABLES_NOTIFICATION_EMAIL=None)
    def test_modify_user(self):
        """
        Check that the username and email fields cannot be modified if the user
        already exists.
        """
        User.objects.create_user(
            username=self.form_data['username'],
            email=self.form_data['email'],
            password=self.form_data['password'],
        )
        self._login(username=self.form_data['username'],
                    password=self.form_data['password'])
        modified = self.form_data.copy()
        modified.update({
            'username': 'snape',
            'email': 'severus.snape@hogwarts.edu',
        })
        self._register(modified)
        application = BetaTestApplication.objects.get()
        self._assert_application_matches_form_data(application)

    @override_settings(VARIABLES_NOTIFICATION_EMAIL='notifications@opencraft.com')
    def test_modifying_design_fields_sends_email(self):
        """
        Check that after an user changes certain fields, we'll get a notification
        e-mail informing of the changes (because we might need to redeploy the
        instance). E.g. after changing colors or other design fields.
        """

        self._register(self.form_data)
        modified = self.form_data.copy()
        original_emails = len(mail.outbox)

        # Modifying most fields shouldn't send an e-mail
        with self.assertTemplateNotUsed('registration/fields_changed_email.txt'):
            modified.update({
                'project_description': 'Learn',
            })
            self._register(modified)
            self.assertEqual(len(mail.outbox), original_emails)

        with self.assertTemplateUsed('registration/fields_changed_email.txt'):
            modified.update({
                'main_color': '#001188',
            })
            self._register(modified)
            self.assertEqual(len(mail.outbox), original_emails + 1)


class BetaTestAjaxValidationTestCase(BetaTestApplicationViewTestMixin,
                                     TestCase):
    """
    Tests the ajax validation view for the beta registration form.
    """
    url = reverse('api:register-list')
    request_method = 'get'

    def _assert_registration_succeeds(self, form_data):
        """
        Check that validating a valid application does not return any errors.
        """
        response = self._register(form_data)
        self.assertJSONEqual(response, '{}')

    @staticmethod
    def _get_error_messages(response):
        """
        Extract error messages from the response JSON.
        """
        return json.loads(response)


class LoginTestCase(UserMixin, TestCase):
    """
    Tests for the login view.
    """
    url = reverse('registration:login')

    def test_login(self):
        """
        Test that users can login.
        """
        response = self.client.post(
            path=self.url,
            data={'username': self.username, 'password': self.password},
            follow=True,
        )
        self.assertEqual(response.context['user'], self.user)

    def test_redirect(self):
        """
        Test that users are redirected to / on login.
        """
        response = self.client.post(
            path=self.url,
            data={'username': self.username, 'password': self.password},
        )
        self.assertRedirects(response, '/', fetch_redirect_response=False)


class LogoutTestCase(UserMixin, TestCase):
    """
    Tests for the logout view.
    """
    url = reverse('registration:logout')

    def setUp(self):
        self.client.login(username=self.username, password=self.password)

    def test_logout(self):
        """
        Test that the logout view logs the user out.
        """
        response = self.client.get(self.url, follow=True)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_redirect(self):
        """
        Test that the logout view redirects to /.
        """
        response = self.client.get(self.url)
        self.assertRedirects(response, '/', fetch_redirect_response=False)
