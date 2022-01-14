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
import binascii
import logging
import os

import dns.resolver as dns_resolver
from django.conf import settings
from django.contrib.auth.models import User
from simple_email_confirmation.models import EmailAddress

from email_verification import send_email_verification
from opencraft.utils import html_email_helper
from registration.models import BetaTestApplication

# Logger  ######################################################################

logger = logging.getLogger(__name__)


# Utilities ###################################################################

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


def send_dns_not_configured_email(application: BetaTestApplication) -> None:
    """
    Send an email with DNS configuration details to the user after detecting
    that the DNS is not configured properly
    """
    user = application.user
    context = dict(
        cname_value=settings.EXTERNAL_DOMAIN_CNAME_VALUE,
        external_domain=application.external_domain
    )
    logger.info("Sending email to %s for DNS Configuration for external domain", user.email)
    html_email_helper(
        template_base_name='emails/dns_not_configured',
        context=context,
        subject="OpenCraft domain verification failed!",
        recipient_list=(user.email,)
    )


def is_external_domain_dns_configured(domain: str) -> bool:
    """
    Checks that there is proper configuration for the external_domain.
    This will check for both domain as well as for the widcard subdomain
    """
    return is_dns_configured(domain) and is_subdomain_dns_configured(domain)


def is_subdomain_dns_configured(domain: str) -> bool:
    """
    Checks that the provided domain has a proper DNS configuration
    for wildcard subdomain i.e. *.{domain}.
    We can use a randomly generated long subdomain to confirm wildcard
    configuration.
    """
    subdomain = '{}.{}'.format(
        binascii.hexlify(os.urandom(20)).decode(),
        domain
    )
    return is_dns_configured(subdomain)


def is_dns_configured(domain: str) -> bool:
    """
    Checks that the provided domain has a proper DNS configuration.
    There should be a CNAME record present with value haproxy.opencraft.hosting
    """

    def get_records(domain_name, record_type):
        try:
            return [str(rdata) for rdata in dns_resolver.resolve(domain_name, record_type)]
        except (dns_resolver.NXDOMAIN, dns_resolver.NoAnswer, dns_resolver.NoNameservers):
            logger.info(
                "DNS not configured for external domain %s in %s",
                domain_name, record_type,
            )

            return []

    cname_records = get_records(domain, 'CNAME')
    if cname_records:
        matching_records = any([
            record == settings.EXTERNAL_DOMAIN_CNAME_VALUE
            for record in cname_records
        ])

        if matching_records:
            return True

    # In case of CloudFlare proxied domains, the CNAME records are flattened and therefore,
    # converted to A records. Since the A records are pointing to CloudFlare name servers,
    # we cannot check them properly. Let's assume that the A records are
    return bool(get_records(domain, 'A'))
