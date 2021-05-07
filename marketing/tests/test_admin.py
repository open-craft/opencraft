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
Tests for marketing app admin actions
"""
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

from marketing.models import EmailTemplate


class SampleEmailActionTestCase(TestCase):
    """
    Tests for send send_sample_email action
    """
    def setUp(self):
        self.email_templates = [
            EmailTemplate.objects.create(
                name="Admin Action Template 1",
                subject="Admin Action Template 1",
                html_body="<h1>Welcome to Opencraft</h1>",
                plaintext_body="Welcome to Opencraft",
                is_active=False,
                send_after_days=1
            ),
            EmailTemplate.objects.create(
                name="Admin Action Template 2",
                subject="Admin Action Template 2",
                html_body="<h1>Welcome to Opencraft</h1>",
                plaintext_body="Welcome to Opencraft",
                is_active=True,
                send_after_days=1
            )
        ]
        self.user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@localhost",
            password="greatadminpassword"
        )

    def test_email_is_sent_for_selected_template(self):
        """
        Tests that email is sent for all selected templates.
        """
        data = {
            "action": "send_sample_emails",
            "_selected_action": [template.pk for template in self.email_templates]
        }
        change_url = reverse("admin:marketing_emailtemplate_changelist")
        self.client.force_login(self.user)
        response = self.client.post(change_url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
