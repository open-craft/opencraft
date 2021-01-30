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
Utility functions related to registration.
"""
import logging

from django.conf import settings
from django.contrib.auth.models import User
from simple_email_confirmation.models import EmailAddress

from email_verification import send_email_verification
from opencraft.utils import html_email_helper
from registration.models import BetaTestApplication


logger = logging.getLogger(__name__)

# Functions #####################################################################


def verify_user_emails(user: User, *email_addresses: str):
    """
    Start email verification process for specified email addresses.

    This should ignore already-verified email addresses.
    """
    for email_address in email_addresses:
        if not EmailAddress.objects.filter(email=email_address).exists():
            email = EmailAddress.objects.create_unconfirmed(email_address, user)
            send_email_verification(email)


def send_welcome_email(application: BetaTestApplication) -> None:
    """
    Send a welcome email to a new user after they have confirmed their email
    addresses.
    """
    user = application.user
    context = dict(
        user_name=user.profile.full_name,
        lms_link=application.instance.get_domain('lms'),
        studio_link=application.instance.get_domain('studio'),
        customise_link=settings.USER_CONSOLE_FRONTEND_URL,
    )
    html_email_helper(
        template_base_name='emails/welcome_email',
        context=context,
        subject=settings.WELCOME_EMAIL_SUBJECT,
        recipient_list=(user.email,)
    )


def send_account_info_email(application: BetaTestApplication) -> None:
    """
    Send an email with account information to a new user after they have
    confirmed their email addresses and their instance is set up.
    """
    user = application.user
    context = dict(
        user_name=user.profile.full_name,
        instance_url=application.instance.get_domain('lms'),
        instance_name=application.instance_name,
        full_name=user.profile.full_name,
        email=user.email,
        public_contact_email=application.public_contact_email,
    )
    html_email_helper(
        template_base_name='emails/account_info_email',
        context=context,
        subject=settings.ACCOUNT_INFO_EMAIL_SUBJECT,
        recipient_list=(user.email,)
    )


def send_changes_deployed_success_email(application: BetaTestApplication) -> None:
    """
    Send an email to user after successful redeployment of the application.
    """
    instance_name = application.instance.name
    user = application.user
    context = dict(
        see_update_url=f"{settings.USER_CONSOLE_FRONTEND_URL}/console/notice"
    )

    recipients = [user.email]

    logger.warning(
        "Sending notification e-mail to %s after instance %s was redeployed",
        recipients,
        instance_name,
    )

    html_email_helper(
        template_base_name='emails/redeployment_success_email',
        context=context,
        subject='Open edX instance deployment: Success',
        recipient_list=recipients
    )
