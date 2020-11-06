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
A Django signal handler to provision a beta tester instance upon successful email confirmation.
"""

# Imports #####################################################################

import logging

from django.conf import settings
from django.db import transaction
from django.dispatch import receiver
from simple_email_confirmation.signals import email_confirmed

from instance.factories import production_instance_factory
from instance.models.deployment import DeploymentType
from instance.utils import create_new_deployment
from registration.models import BetaTestApplication
from registration.utils import send_account_info_email

# Logging #####################################################################
logger = logging.getLogger(__name__)


# Signal handler ##############################################################


@receiver(email_confirmed)
def provision_instance(sender, **kwargs):
    """
    Provision a new instance once all email addresses of a user are confirmed.
    This method wraps _provision_instance so that we can mock it out more easily
    for testing purposes.
    """
    _provision_instance(sender, **kwargs)


def _provision_instance(sender, **kwargs):
    """Provision a new instance once all email addresses of a user are confirmed."""
    user = sender
    if not all(email.is_confirmed for email in user.email_address_set.iterator()):
        return
    try:
        application = user.betatestapplication
    except BetaTestApplication.DoesNotExist:
        logger.info('Email confirmed for user %s, who is not a beta tester.', user.username)
        return
    if application.status == BetaTestApplication.REJECTED:
        logger.info('Email confirmed for user %s, but application was rejected.', user.username)
        return
    if application.instance is not None:
        logger.info('Email confirmed for user %s, but instance already provisioned.', user.username)
        return

    with transaction.atomic():
        application.instance = production_instance_factory(
            sub_domain=application.subdomain,
            name=application.instance_name,
            email=application.public_contact_email,
            privacy_policy_url=application.privacy_policy_url,
        )
        application.instance.lms_users.add(user)
        application.instance.ref.creator = user.profile
        application.instance.ref.save()

        # Check if simple theme is set up and add it to instance
        if application.draft_theme_config:
            application.instance.theme_config = application.draft_theme_config
            application.instance.deploy_simpletheme = True
            application.instance.save()

        # If using external domain, set it up
        if application.external_domain:
            application.instance.external_lms_domain = application.external_domain
            application.instance.save()

        if settings.PROD_APPSERVER_FAIL_EMAILS:
            application.instance.provisioning_failure_notification_emails = settings.PROD_APPSERVER_FAIL_EMAILS
            application.instance.additional_monitoring_emails = settings.PROD_APPSERVER_FAIL_EMAILS
            application.instance.save()
        application.save()
        # At this point we know the user has confirmed their email and set up an instance.
        # So we can go ahead and send the account info email.
        transaction.on_commit(lambda: send_account_info_email(application))
    create_new_deployment(
        application.instance,
        mark_active_on_success=True,
        num_attempts=2,
        creator=user,
        deployment_type=DeploymentType.registration,
    )
