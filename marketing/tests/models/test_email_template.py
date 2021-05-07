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
Test for marketing model EmailTemplate
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

from marketing.models import EmailTemplate


class EmailTemplateTestCase(TestCase):
    """
    Test for model EmailTemplate.
    """

    def setUp(self):
        self.template = EmailTemplate.objects.create(
            name="Test Template 1",
            subject="Test Template subject",
            html_body="<h1>Welcome to Opencraft.</h1>",
            plaintext_body="Welcome to Opencraft.",
            is_active=True,
            send_after_days=5
        )

    def test_str_representation(self):
        """
        Test that the string representation is template.name
        """
        self.assertEqual(str(self.template), self.template.name)

    def test_subject_template_returns_correct_template(self):
        """
        Test that the subject_template has correct source
        """
        subject_template = self.template.subject_template
        # Template source is subject.
        self.assertEqual(subject_template.source, self.template.subject)

    def test_body_template_returns_correct_template(self):
        """
        Test that the body templates return templates with correct source
        """
        html_body_template = self.template.html_body_template
        plaintext_body_template = self.template.plaintext_body_template
        self.assertEqual(html_body_template.source, self.template.html_body)
        self.assertEqual(plaintext_body_template.source, self.template.plaintext_body)

    def test_send_after_days_validation(self):
        """
        Test that the send_after_days cannot be set greater than
        settings.MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS
        """
        with self.assertRaises(ValidationError) as error:
            EmailTemplate(
                name="Bad Template",
                subject="Bad Template Subject",
                html_body="<h1>Template</h1>",
                plaintext_body="Template",
                is_active=False,
                send_after_days=settings.MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS + 1
            ).full_clean()
        expected_message = "Configuring follow up email after {} days is not allowed.".format(
            settings.MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS
        )
        self.assertIn(expected_message, error.exception.messages)

        with self.assertRaises(ValidationError) as error:
            EmailTemplate(
                name="Bad Template",
                subject="Bad Template Subject",
                html_body="<h1>Template</h1>",
                plaintext_body="Template",
                is_active=False,
                send_after_days=0
            ).full_clean()
        expected_message = "Ensure this value is greater than or equal to 1."
        self.assertIn(expected_message, error.exception.messages)
