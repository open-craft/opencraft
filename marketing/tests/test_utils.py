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
Tests for marketing utils
"""
from unittest.mock import patch
from smtplib import SMTPException

from django.test import TestCase
from django.test import override_settings

from marketing.models import SentEmail, EmailTemplate, Subscriber
from marketing.utils import render_and_dispatch_email
from instance.tests.base import create_user_and_profile
from registration.models import BetaTestApplication


class RenderDispatchMailTestCase(TestCase):
    """
    Tests for render_and_dispatch_email utility function
    """

    def setUp(self):
        self.user = create_user_and_profile('test_user', 'test_user@example.com')
        BetaTestApplication.objects.create(
            user=self.user,
            subdomain='somedomain',
            instance_name="User Instance",
            public_contact_email='test_user@example.com',
            privacy_policy_url='http://www.some/url'
        )
        self.subscriber = Subscriber.objects.create(user=self.user)
        self.template = EmailTemplate.objects.create(
            name="Template 1",
            subject="Attention! {{instance_name}} owner",
            html_body="<p>Hi {{username}}, your instance {{instance_name}} is ready.</p>",
            plaintext_body="Hi {{username}}, your instance {{instance_name}} is ready.",
            is_active=True,
            send_after_days=5
        )

    @patch('marketing.utils.send_mail')
    def test_sent_email_is_saved_if_successful(self, mock_send_mail):
        """
        Tests that email is saved after sending.
        """
        render_and_dispatch_email(self.template, self.subscriber)
        mock_send_mail.assert_called_once()
        self.assertEqual(SentEmail.objects.count(), 1)

        mock_send_mail.side_effect = SMTPException("Cannot sent Email")
        render_and_dispatch_email(self.template, self.subscriber)
        self.assertEqual(SentEmail.objects.count(), 1)

    @override_settings(MARKETING_EMAIL_SENDER='marketing@opencraft.com')
    @patch('marketing.utils.send_mail')
    def test_email_is_rendered_properly(self, mock_send_mail):
        """
        Tests that subject, html_body and plaintext_body is rendered
        correctly
        """
        render_and_dispatch_email(self.template, self.subscriber)
        mock_send_mail.assert_called_once_with(
            subject="Attention! User Instance owner",
            message="Hi test_user, your instance User Instance is ready.",
            html_message="<p>Hi test_user, your instance User Instance is ready.</p>",
            from_email="marketing@opencraft.com",
            recipient_list=[self.user.email],
        )
