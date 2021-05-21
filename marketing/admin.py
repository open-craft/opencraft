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
Admin for the marketing app
"""
import smtplib

from django.conf import settings
from django.contrib import admin
from django.core.mail import send_mail
from django.template import Context

from marketing import models
from registration.models import BetaTestApplication


class EmailTemplateAdmin(admin.ModelAdmin): #pylint: disable=missing-docstring
    list_display = ("id", "name", "subject", "is_active")

    actions = ['send_sample_emails']

    def send_sample_emails(self, request, queryset):
        """
        Action to send sample emails to the staff user with dummy
        BetaTestApplication data.
        """
        dummy_application = BetaTestApplication(
            user=request.user,
            subdomain="dummy-subdomain",
            instance_name="EmailTemplate Sample"
        )
        context = Context({
            "full_name": request.user.get_full_name(),
            "username": request.user.username,
            "instance_name": "EmailTemplate Sample",
            "subdomain": "dummy-subdomain",
            "application": dummy_application
        })
        for template in queryset:
            subject = template.subject_template.render(context)
            html_body = template.html_body_template.render(context)
            plaintext_body = template.plaintext_body_template.render(context)
            try:
                send_mail(
                    subject=subject,
                    message=plaintext_body,
                    html_message=html_body,
                    from_email=settings.MARKETING_EMAIL_SENDER,
                    recipient_list=[request.user.email],
                )
            except smtplib.SMTPException:
                self.message_user(request, "Failed to send template: %s", template)
        self.message_user(request, "Successfully sent sample emails.")

    send_sample_emails.short_description = "Send sample emails for selected email templates"


class SubscriberAdmin(admin.ModelAdmin): #pylint: disable=missing-docstring
    list_display = ("user", "receive_followup", "trial_started_at")
    list_filter = ("receive_followup", )


class SentEmailAdmin(admin.ModelAdmin): #pylint: disable=missing-docstring
    list_display = ("id", "user", "template", "sent_at")
    # Don't Allow Email modification after sent
    readonly_fields = [field.name for field in models.SentEmail._meta.get_fields(include_parents=True)]


admin.site.register(models.SentEmail, SentEmailAdmin)
admin.site.register(models.Subscriber, SubscriberAdmin)
admin.site.register(models.EmailTemplate, EmailTemplateAdmin)
