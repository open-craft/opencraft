# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <contact@opencraft.com>
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
Test password reset flow for Ocim console.
"""
from collections import namedtuple

from django.conf import settings
from django.core import mail as django_mail
from django_rest_passwordreset.models import ResetPasswordToken
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC  # nopep8
from selenium.common.exceptions import NoSuchElementException
from simple_email_confirmation.models import EmailAddress

from e2e_tests.tests.utils import BrowserLiveServerTestCase
from instance.tests.base import create_user_and_profile
from registration.models import BetaTestApplication


class ForgotPasswordTestCase(BrowserLiveServerTestCase):
    """
    Tests the forgot passwor page.
    """

    def setUp(self):
        """
        Setup the user with a BetaTestApplication
        """
        super().setUp()
        self.user_with_app = create_user_and_profile('jerry.mouse', 'jerry.mouse@example.com')
        self.application = BetaTestApplication.objects.create(
            user=self.user_with_app,
            subdomain="cheese-school",
            instance_name="Jerry's School of Cheese",
            public_contact_email="jerry.mouse@example.com",
            privacy_policy_url="http://www.some/url"
        )
        EmailAddress.objects.create_confirmed(
            email=self.application.public_contact_email,
            user=self.user_with_app,
        )
        self.forgot_password_url = f"{settings.USER_CONSOLE_FRONTEND_URL}/password-forgotten"

    def _open_forgot_password_page(self):
        """
        Opens the forgot password page and returns form
        WebElements
        """
        self.browser.get(self.forgot_password_url)
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )

        email_field = self.form.find_element_by_name("email")
        reset_password_btn = self.form.find_element_by_tag_name("button")
        return email_field, reset_password_btn

    @property
    def form(self):
        """
        Get the form element on the page
        """
        return self.browser.find_element_by_tag_name("form")

    def test_forgot_password_page_loads_successfully(self):
        """
        Tests that the reset password page loads correctly
        """
        # Jerry visits the forgot password page
        email_field, reset_password_btn = self._open_forgot_password_page()

        # Jerry can see a email input and a reset password button
        self.assertTrue(email_field.is_displayed())
        self.assertTrue(reset_password_btn.is_displayed())
        # Text of the button is "reset password"
        self.assertEqual(reset_password_btn.text.lower(), "reset password")

    def test_empty_email_error(self):
        """
        Tests error message is displayed to used for
        empty email field
        """
        # Jerry mouse visits the forgot password page
        _, reset_password_btn = self._open_forgot_password_page()
        # Jerry clicks the reset password button
        reset_password_btn.click()
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        )
        alert_element = self.form.find_element_by_class_name('alert-danger')
        # Jerry is shown an error message saying this "field may not be blank"
        self.assertTrue(alert_element.is_displayed())
        self.assertTrue(alert_element.text.lower(), "this field may not be blank")

    def test_invalid_email_error(self):
        """
        Test error is shown to user on invalid email
        submission
        """
        # Jerry Mouse visits the forgot password page
        email_field, reset_password_btn = self._open_forgot_password_page()

        # Jerry enters a invalid email in email_field
        email_field.send_keys("jerry.mouse")
        # Jerry clicks reset password button
        reset_password_btn.click()
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        )
        alert_element = self.form.find_element_by_class_name('alert-danger')
        # Jerry is shown an error message saying "enter a valid email address"
        self.assertTrue(alert_element.is_displayed())
        self.assertTrue(alert_element.text.lower(), "enter a valid email address")

    def test_forgot_password_email_sent_for_existing_user_email(self):
        """
        Test that user is shown a success message on valid email
        submission and an email is triggered if user with
        email exists.
        """
        # Jerry Mouse visits the forgot password page
        email_field, reset_password_btn = self._open_forgot_password_page()

        # Jerry enters his email in email_field and clicks reset password button
        email_field.send_keys("jerry.mouse@example.com")
        reset_password_btn.click()
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-success'))
        )
        alert_element = self.form.find_element_by_class_name('alert-success')
        # Jerry is shown a success message about reset email sent.
        self.assertTrue(alert_element.is_displayed())
        self.assertIn("password reset link sent by email", alert_element.text.lower())

        # An email is sent with appropriate subject
        self.assertEqual(len(django_mail.outbox), 1)
        mail = django_mail.outbox[0]
        self.assertEqual(mail.subject, settings.RESET_PASSWORD_EMAIL_SUBJECT)

    def test_no_email_sent_with_non_existing_user_email(self):
        """
        Test that user is shown a success message on valid email
        submission even if user does not exits,
        and an email is not triggered in this case.
        """
        # Jerry Mouse visits the forgot password page
        email_field, reset_password_btn = self._open_forgot_password_page()

        # Jerry enters Tom Cat's email in email_field and clicks reset password button
        email_field.send_keys("tom.cat@example.com")
        reset_password_btn.click()
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-success'))
        )
        alert_element = self.form.find_element_by_class_name('alert-success')
        # Jerry is shown a success message about reset email sent.
        # We do not show an error and expose information.
        self.assertTrue(alert_element.is_displayed())
        self.assertIn("password reset link sent by email", alert_element.text.lower())

        # Since Tom Cat is not a user, we do not send an email.
        self.assertEqual(len(django_mail.outbox), 0)


class ResetPasswordConfirmTestCase(BrowserLiveServerTestCase):
    """
    Test the reset password page.
    """

    FormTuple = namedtuple('Form', ['form', 'password_field', 'password_confirm_field', 'submit_btn'])

    def setUp(self):
        super().setUp()
        self.user_with_app = create_user_and_profile('jerry.mouse', 'jerry.mouse@example.com')
        self.application = BetaTestApplication.objects.create(
            user=self.user_with_app,
            subdomain="cheese-school",
            instance_name="Jerry's School of Cheese",
            public_contact_email="jerry.mouse@example.com",
            privacy_policy_url="http://www.some/url"
        )
        EmailAddress.objects.create_confirmed(
            email=self.application.public_contact_email,
            user=self.user_with_app,
        )
        self.reset_password_token = ResetPasswordToken.objects.create(user=self.user_with_app)
        self.confirm_token_page_url = f"{settings.USER_CONSOLE_FRONTEND_URL}/password-reset/" + "{token}"
        self.login_page_url = f"{settings.USER_CONSOLE_FRONTEND_URL}/login"
        self.console_home_url = f"{settings.USER_CONSOLE_FRONTEND_URL}/console"
        self.strong_password = "Tom&Jerry2021"

    @property
    def form(self):
        """
        Get the form element on the page
        """
        form = self.browser.find_element_by_tag_name("form")
        password_field = form.find_element_by_name("password")
        password_confirm_field = form.find_element_by_name('passwordConfirm')
        submit_btn = form.find_element_by_tag_name('button')
        return self.FormTuple(form, password_field, password_confirm_field, submit_btn)

    def _open_password_reset_with_token(self, token):
        """
        Opens the url and waits for spinner to appear and then disapper
        """
        url = self.confirm_token_page_url.format(token=token)
        self.browser.get(url)
        self.wait.until(
            EC.invisibility_of_element_located((By.CLASS_NAME, 'spinner'))
        )

    def _assert_strong_password_alert(self, alert_text):
        """
        Tests basic weak password warnings.
        """
        self.assertIn('too short', alert_text)
        self.assertIn('at least 9 characters', alert_text)
        self.assertIn('at least 1 uppercase letter', alert_text)
        self.assertIn('at least 1 special character', alert_text)

    def test_invalid_token_error(self):
        """
        Tests that the form is not shown on invalid token and
        an error message is displayed.
        """
        # Jerry Mouse tires a password reset link with random invalid token
        self._open_password_reset_with_token("token_of_tom")
        # Jerry doesn't see the change password form
        with self.assertRaises(NoSuchElementException):
            _ = self.form
        # Instead he sees the invalid token message.
        message = self.browser.find_element_by_class_name('content-page-content')
        self.assertTrue(message.is_displayed())
        self.assertIn('invalid or expired', message.text.lower())

    def test_new_password_form_visible_on_valid_token(self):
        """
        Tests that the new password form is visible for valid token
        """
        # Jerry Mouse opens the reset form url
        self._open_password_reset_with_token(self.reset_password_token.key)
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )
        form = self.form

        # Jerry Mouse sees a reset form
        self.assertTrue(form.form.is_displayed())
        self.assertTrue(form.password_field.is_displayed())
        self.assertTrue(form.password_confirm_field.is_displayed())
        self.assertTrue(form.submit_btn.is_displayed())
        # Submit button is disabled
        self.assertFalse(form.submit_btn.is_enabled())

    def test_both_fields_should_have_same_values(self):
        """
        Tests that the password and passwordConfirm fields have
        the same value.
        """
        # Jerry Mouse opens the reset form url
        self._open_password_reset_with_token(self.reset_password_token.key)
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )
        form = self.form

        # Jerry Mouse enters his new password in password_field
        form.password_field.send_keys("jerrylovescheese")
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        )
        alert_element = form.form.find_element_by_class_name('alert-danger')
        # Jerry sees the alert and inactive submit_btn
        self.assertTrue(alert_element.is_displayed())
        self.assertFalse(form.submit_btn.is_enabled())
        self.assertIn('do not match', alert_element.text.lower())

        # Jerry Mouse enters his new password in password_confirm_field
        # which does not match his other entry
        form.password_confirm_field.send_keys("jerryLovesCheese")
        # Jerry still sees the alert message
        self.assertTrue(alert_element.is_displayed())
        self.assertFalse(form.submit_btn.is_enabled())
        # Jerry enters the same password in both fields
        form.password_confirm_field.clear()
        form.password_confirm_field.send_keys("jerrylovescheese")
        self.wait.until_not(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        )
        # The alert message disapears and submit button becomes active.
        self.assertTrue(form.submit_btn.is_enabled())

    def test_error_on_weak_passwords(self):
        """
        Test that an error is shown on weak passwords
        """
        # Jerry Mouse opens the reset form url
        self._open_password_reset_with_token(self.reset_password_token.key)
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )
        form = self.form
        # Jerry enters his new password in both fields and submits
        form.password_field.send_keys("nibbles")
        form.password_confirm_field.send_keys("nibbles")
        form.submit_btn.click()
        self.wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert-danger'))
        )

        # Jerry sees an alert div with multiple error messages
        alert_element = form.form.find_element_by_class_name('alert-danger')
        alert_text = alert_element.text.lower()
        self.assertTrue(alert_element.is_displayed())
        self._assert_strong_password_alert(alert_text)

    def test_password_changed_on_strong_password(self):
        """
        Tests that the password is correct.
        Checks that the password is reset by completing login
        """
        # Jerry Mouse opens the reset form url
        self._open_password_reset_with_token(self.reset_password_token.key)
        self.wait.until(
            EC.presence_of_element_located((By.TAG_NAME, 'form'))
        )
        form = self.form
        # Jerry enters his new strong password in both fields and submits
        form.password_field.send_keys(self.strong_password)
        form.password_confirm_field.send_keys(self.strong_password)
        form.submit_btn.click()
        current_url = self.confirm_token_page_url.format(token=self.reset_password_token.key)
        self.wait.until(
            EC.url_changes((By.CLASS_NAME, current_url))
        )

        # Jerry Mouse is redirected to login page with success message.
        self.assertEqual(self.browser.current_url, self.login_page_url)

        login_form = self.browser.find_element_by_tag_name('form')
        self.assertTrue(login_form.is_displayed())
        username_field = login_form.find_element_by_name('username')
        password_field = login_form.find_element_by_name('password')
        submit_btn = login_form.find_element_by_tag_name('button')
        alert_element = login_form.find_element_by_class_name('alert-success')

        self.assertIn('your password has been reset', alert_element.text.lower())

        # Jerry Mouse enters his new credentials and is successfully logged in
        username_field.send_keys('jerry.mouse')
        password_field.send_keys(self.strong_password)
        submit_btn.click()
        self.wait.until(
            EC.url_changes(self.login_page_url)
        )

        self.assertEqual(self.browser.current_url, self.console_home_url)
