# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
General utility functions for OCIM.
"""
from typing import Any, Dict, Iterable, Optional

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import get_template


def get_site_url(relative_path: str = '') -> str:
    """
    Uses the site framework to build an absolute URL.

    This function can be used to build an absolute URL for the site without
    needing access to the request object.
    """
    domain = get_current_site(request=None).domain
    if settings.DEBUG or 'localhost' in domain:
        scheme = "http"
    else:
        scheme = "https"
    return f"{scheme}://{domain}{relative_path}"


def build_email_context(
        context: Optional[Dict[str, str]] = None,
        subject: Optional[str] = None,
) -> Dict[str, str]:
    """
    Builds a context object with common settings for emails.

    Fills in the common configuration variables needed by most email templates.
    The values provided in context override the values this function fills in.
    """
    combined_context = dict(
        base_url=get_site_url(),
        signature_title=settings.EMAIL_SIGNATURE_TITLE,
        signature_name=settings.EMAIL_SIGNATURE_NAME,
        subject=subject,
    )
    if context is not None:
        combined_context.update(context)
    return combined_context


def html_email_helper(template_base_name: str, context: Dict[str, Any], subject: str,
                      recipient_list: Iterable[str], from_email: str = None):
    """
    A helper function for sending HTML emails.

    @param template_base_name: Base template path. The function will append .txt and .html
           to get the appropriate templates for the text and html parts of the email respectively.
    @param context: The context to pass to the email. Automatically includes common context
           needed by emails.
    @param subject: Email subject.
    @param recipient_list: List of email addresses.
    @param from_email: The sender of the email. Uses default if nothing is passed.
    """
    email_context = build_email_context(context, subject=subject)

    text_template = get_template(f'{template_base_name}.txt')
    text_message = text_template.render(email_context)

    html_template = get_template(f'{template_base_name}.html')
    html_message = html_template.render(email_context)

    send_mail(
        subject=subject,
        message=text_message,
        html_message=html_message,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
    )
