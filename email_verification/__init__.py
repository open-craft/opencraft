# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.urls import reverse


# Settings ####################################################################

EMAIL_VERIFICATION_SENDER = getattr(settings, 'EMAIL_VERIFICATION_SENDER',
                                    settings.DEFAULT_FROM_EMAIL)
EMAIL_VERIFICATION_SUBJECT = getattr(settings, 'EMAIL_VERIFICATION_SUBJECT',
                                     'Please verify this email address')
EMAIL_VERIFICATION_TEMPLATE = getattr(settings, 'EMAIL_VERIFICATION_TEMPLATE',
                                      'email_verification/email.txt')


# Functions ###################################################################

def send_email_verification(email, request):
    """
    Verify the given `EmailAddress`.
    """
    verification_url = reverse('email-verification:verify', kwargs={
        'code': email.key,
    })
    template = get_template(EMAIL_VERIFICATION_TEMPLATE)
    message = template.render({
        'email': email,
        'verification_url': request.build_absolute_uri(verification_url),
    }, request)
    send_mail(
        subject=EMAIL_VERIFICATION_SUBJECT,
        message=message,
        from_email=EMAIL_VERIFICATION_SENDER,
        recipient_list=(email.email,),
    )
