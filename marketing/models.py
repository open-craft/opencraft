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
Model definitions for marketing and followup email
campaigns.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.template import Template
from django.utils.functional import cached_property
from django.utils.timezone import now


def validate_send_after_days_max_value(value):
    """
    Validate that the `value` is lower than MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS.
    Otherwise emails will be repeatedly sent since the cleanup job will clear those emails
    """
    if value > settings.MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS:
        raise ValidationError(
            "Configuring follow up email after {} days is not allowed.".format(
                settings.MARKETING_DELETE_FOLLOWUP_EMAILS_AFTER_DAYS
            )
        )


class EmailTemplate(models.Model):
    """
    Model to store the Email templates
    """
    name = models.CharField(
        unique=True,
        max_length=100,
        help_text="Name of the email template. It can be used as an identifier for emails. Must be unique."
    )
    subject = models.CharField(
        max_length=256,
        help_text="Template for the subject of email"
    )
    html_body = models.TextField(
        help_text="Template for the html body of the email."
    )
    plaintext_body = models.TextField(
        help_text="Template for the text body of the email."
    )
    is_active = models.BooleanField(
        default=False,
        help_text="If the email is active or not. Emails will be sent for active templates only."
    )
    send_after_days = models.IntegerField(
        validators=[
            MinValueValidator(1),
            validate_send_after_days_max_value
        ],
        help_text="Number of days after instance activation the email will be sent"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        String representation
        """
        return self.name

    @cached_property
    def subject_template(self):
        """
        Get Template instance for subject.
        """
        return Template(self.subject)

    @cached_property
    def html_body_template(self):
        """
        Get Template instance for html_body.
        """
        return Template(self.html_body)

    @cached_property
    def plaintext_body_template(self):
        """
        Get Template instance for plaintext_body.
        """
        return Template(self.plaintext_body)


class SentEmail(models.Model):
    """
    Model to store sent followup emails.
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    email_subject = models.TextField()
    email_html_body = models.TextField()
    email_plaintext_body = models.TextField()
    sent_at = models.DateTimeField(default=now)

    def __str__(self):
        """
        String representation
        """
        return "{recipient}<EmailTemplate={template}>".format(
            recipient=self.user_id,
            template=str(self.template)
        )


class Subscriber(models.Model):
    """
    Model to store followup email subscribers
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    receive_followup = models.BooleanField(
        default=True,
        help_text="Should the user receive followup emails?"
    )
    trial_started_at = models.DateTimeField(
        default=now,
        help_text="Datetime when first appserver became active"
    )

    def __str__(self):
        """
        String representation.
        """
        return self.user.email
