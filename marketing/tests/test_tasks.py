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
Test for marketing huey tasks.
"""
from datetime import timedelta
from unittest.mock import patch, call

from django.test import TestCase, override_settings
from django.utils.timezone import now

from marketing.models import SentEmail, EmailTemplate, Subscriber
from marketing.tasks import prune_emails, send_followup_emails
from instance.tests.base import create_user_and_profile
from registration.models import BetaTestApplication


class PurgeSentEmailTestCase(TestCase):
    """
    Tests for prune_emails task
    """

    def setUp(self):
        self.test_user = create_user_and_profile('test_user', 'test_user@example.com')
        self.email_template = EmailTemplate.objects.create(
            name="Test Template",
            subject="Welcome",
            html_body="<h1>Welcome to Opencraft</h1>",
            plaintext_body="Welcome to Opencraft",
            is_active=True,
            send_after_days=5
        )
        self.day_delta_list = [0, 4, 10, 20, 25, 31, 35, 40, 45]
        self._create_sent_emails(self.day_delta_list)

    def tearDown(self):
        self._clear_sent_emails()

    def _clear_sent_emails(self):
        """
        Clear all records in SentEmail model.
        """
        SentEmail.objects.all().delete()

    def _create_sent_emails(self, day_delta_list):
        """
        Creates instances of SentEmail with past sent_at
        dates.
        """
        for delta in day_delta_list:
            sent_at = now() - timedelta(days=delta)
            SentEmail.objects.create(
                user=self.test_user,
                template=self.email_template,
                sent_at=sent_at
            )

    def test_recent_emails_are_not_deleted(self):
        """
        Tests that prune_emails deletes old emails.
        """
        self.assertEqual(SentEmail.objects.count(), len(self.day_delta_list))
        prune_emails()
        self.assertEqual(SentEmail.objects.count(), 5)

    @override_settings(MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS=5)
    def test_prune_emails_config_setting(self):
        """
        Test that prune emails is configurable using setting
        MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS
        """
        self.assertEqual(SentEmail.objects.count(), len(self.day_delta_list))
        prune_emails()
        self.assertEqual(SentEmail.objects.count(), 2)


class SendFollowupTestCase(TestCase):
    """
    Tests for send_followup_emails task
    """

    def setUp(self):
        self.test_user_1 = create_user_and_profile('test_user', 'test_user1@example.com')
        self.test_user_2 = create_user_and_profile('test_user_2', 'test_user2@example.com')
        self.test_user_3 = create_user_and_profile('test_user_3', 'test_user3@example.com')
        self.test_user_4 = create_user_and_profile('test_user_4', 'test_user4@example.com')
        BetaTestApplication.objects.create(
            user=self.test_user_1,
            subdomain='user1',
            instance_name="User1 Instance",
            public_contact_email='test_user1@example.com',
            privacy_policy_url='http://www.some/url'
        )
        BetaTestApplication.objects.create(
            user=self.test_user_2,
            subdomain='user2',
            instance_name="User2 Instance",
            public_contact_email='test_user2@example.com',
            privacy_policy_url='http://www.some/url'
        )
        BetaTestApplication.objects.create(
            user=self.test_user_3,
            subdomain='user3',
            instance_name="User3 Instance",
            public_contact_email='test_user3@example.com',
            privacy_policy_url='http://www.some/url'
        )
        BetaTestApplication.objects.create(
            user=self.test_user_4,
            subdomain='user4',
            instance_name="User4 Instance",
            public_contact_email='test_user4@example.com',
            privacy_policy_url='http://www.some/url'
        )
        self.active_subscriber_1 = Subscriber.objects.create(
            user=self.test_user_1,
            receive_followup=True,
            trial_started_at=now() - timedelta(days=5)
        )
        self.active_subscriber_2 = Subscriber.objects.create(
            user=self.test_user_2,
            receive_followup=True,
            trial_started_at=now() - timedelta(days=2)
        )
        self.inactive_subscriber_1 = Subscriber.objects.create(
            user=self.test_user_3,
            receive_followup=False,
            trial_started_at=now() - timedelta(days=5)
        )
        self.inactive_subscriber_2 = Subscriber.objects.create(
            user=self.test_user_4,
            receive_followup=False,
            trial_started_at=now() - timedelta(days=2)
        )
        self.active_email_template = EmailTemplate.objects.create(
            name="Template 1",
            subject="Template 1",
            html_body="<h1>Welcome to Opencraft</h1>",
            plaintext_body="Welcome to Opencraft",
            is_active=True,
            send_after_days=5
        )
        self.inactive_email_template = EmailTemplate.objects.create(
            name="Template 2",
            subject="Template 2",
            html_body="<p>Welcome</p>",
            plaintext_body="Welcome",
            is_active=False,
            send_after_days=2
        )

    def tearDown(self):
        SentEmail.objects.all().delete()

    @patch('marketing.tasks.render_and_dispatch_email')
    def test_email_is_sent_to_subscribed_users(self, mock_dispatch):
        """
        Test that email will be sent to subscribers with receive_followup
        set to true.
        """
        send_followup_emails()
        expected_calls = [
            call(self.active_email_template, self.active_subscriber_1)
        ]
        mock_dispatch.assert_has_calls(expected_calls, any_order=True)
        mock_dispatch.reset_mock()

        # activate inactive_subscriber_1
        self.inactive_subscriber_1.receive_followup = True
        self.inactive_subscriber_1.save()

        send_followup_emails()
        expected_calls = [
            call(self.active_email_template, self.active_subscriber_1),
            call(self.active_email_template, self.inactive_subscriber_1)
        ]
        mock_dispatch.assert_has_calls(expected_calls, any_order=True)

    @patch('marketing.tasks.render_and_dispatch_email')
    def test_email_is_not_sent_if_already_in_sent_emails(self, mock_dispatch):
        """
        Tests that email is only sent if user does not have a SentEmail
        with active template.
        """
        # Create a sent email record
        SentEmail.objects.create(
            user=self.test_user_1,
            template=self.active_email_template
        )
        send_followup_emails()
        mock_dispatch.assert_not_called()

    @patch('marketing.tasks.render_and_dispatch_email')
    def test_email_is_not_sent_to_users_unsubscribed(self, mock_dispatch):
        """
        Test that the email is not sent for subscribers with
        receive_followup set to false.
        """
        send_followup_emails()
        not_expected_calls = [
            call(self.active_email_template, self.inactive_subscriber_1),
            call(self.active_email_template, self.inactive_subscriber_2)
        ]
        all_calls = mock_dispatch.call_args_list
        assert not any([not_expected in all_calls for not_expected in not_expected_calls])

    @patch('marketing.tasks.render_and_dispatch_email')
    def test_email_is_sent_for_active_templates_only(self, mock_dispatch):
        """
        Test that email is sent for all active email templates
        """
        send_followup_emails()
        expected_calls = [
            call(self.active_email_template, self.active_subscriber_1),
        ]
        mock_dispatch.assert_has_calls(expected_calls, any_order=True)

        mock_dispatch.reset_mock()
        # activate second template
        self.inactive_email_template.is_active = True
        self.inactive_email_template.save()
        send_followup_emails()
        expected_calls = [
            call(self.active_email_template, self.active_subscriber_1,),
            call(self.inactive_email_template, self.active_subscriber_2)
        ]
        not_expected_calls = [
            call(self.active_email_template, self.inactive_subscriber_1),
            call(self.inactive_email_template, self.inactive_subscriber_2)
        ]
        mock_dispatch.assert_has_calls(expected_calls, any_order=True)
        all_calls = mock_dispatch.call_args_list
        assert not any([not_expected in all_calls for not_expected in not_expected_calls])
