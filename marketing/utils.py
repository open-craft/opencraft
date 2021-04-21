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
Utility function for marketing app
"""

import smtplib
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context

from marketing.models import Subscriber, EmailTemplate, SentEmail


# Logging #####################################################################

logger = logging.getLogger(__name__)


def render_and_dispatch_email(template: EmailTemplate, subscriber: Subscriber):
    """
    Given an EmailTemplate and Subscriber, renders the email from
    template and sends the email.
    """
    application = subscriber.user.betatestapplication
    user = subscriber.user
    context = Context({
        "full_name": user.profile.full_name,
        "username": user.get_username(),
        "instance_name": application.instance_name,
        "subdomain": application.subdomain,
        "application": application
    })
    subject = template.subject_template.render(context)
    html_body = template.html_body_template.render(context)
    plaintext_body = template.plaintext_body_template.render(context)

    try:
        send_mail(
            subject=subject,
            message=plaintext_body,
            html_message=html_body,
            from_email=settings.MARKETING_EMAIL_SENDER,
            recipient_list=[user.email],
        )
    except smtplib.SMTPException:
        logger.error("Failed to send followup email '%s' to %s", template.name, user.email)
    else:
        SentEmail.objects.create(
            user=user,
            template=template,
            email_subject=subject,
            email_html_body=html_body,
            email_plaintext_body=plaintext_body,
        )
