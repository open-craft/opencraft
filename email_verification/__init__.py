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
Email verification
"""

# Imports #####################################################################

from typing import TYPE_CHECKING
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse

from opencraft.utils import html_email_helper

if TYPE_CHECKING:
    from simple_email_confirmation.models import EmailAddress

# Settings ####################################################################

EMAIL_VERIFICATION_SENDER = getattr(settings, 'EMAIL_VERIFICATION_SENDER',
                                    settings.DEFAULT_FROM_EMAIL)
EMAIL_VERIFICATION_SUBJECT = getattr(settings, 'EMAIL_VERIFICATION_SUBJECT',
                                     'Please verify this email address')
EMAIL_VERIFICATION_TEMPLATE = getattr(settings, 'EMAIL_VERIFICATION_TEMPLATE',
                                      'emails/verify_email')


# Functions ###################################################################

def send_email_verification(email: "EmailAddress"):
    """
    Verify the given `EmailAddress`.

    The verification link points to the frontend, which then
    uses the Email verification viewset to make a request to
    the backend and activate the email.
    """
    verification_url = urljoin(
        settings.USER_CONSOLE_FRONTEND_URL,
        f"/verify-email/{email.key}"
    )
    html_email_helper(
        template_base_name=EMAIL_VERIFICATION_TEMPLATE,
        context={'verification_url': verification_url},
        subject=EMAIL_VERIFICATION_SUBJECT,
        recipient_list=(email.email,),
        from_email=EMAIL_VERIFICATION_SENDER,
    )
