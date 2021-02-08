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
Signals related to registration.
"""
from django.conf import settings
from django.dispatch import receiver
from django_rest_passwordreset.models import ResetPasswordToken
from django_rest_passwordreset.signals import reset_password_token_created
from django_rest_passwordreset.views import ResetPasswordRequestToken

from instance.models.deployment import Deployment, DeploymentType
from instance.signals import appserver_spawned
from opencraft.utils import html_email_helper
from registration.models import BetaTestApplication
from registration.utils import send_changes_deployed_success_email


# noinspection PyUnusedLocal
@receiver(reset_password_token_created)
def password_reset_token_created(
        sender: ResetPasswordRequestToken,
        instance: ResetPasswordRequestToken,
        reset_password_token: ResetPasswordToken,
        *_args,
        **_kwargs,
) -> None:
    """
    Handles password reset tokens.
    When a token is created, an e-mail is sent to the user

    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    """
    context = dict(
        reset_password_url=f"{settings.USER_CONSOLE_FRONTEND_URL}/password-reset/{reset_password_token.key}"
    )
    html_email_helper(
        template_base_name='emails/reset_password_email',
        context=context,
        subject=settings.RESET_PASSWORD_EMAIL_SUBJECT,
        recipient_list=(reset_password_token.user.email,)
    )


@receiver(appserver_spawned)
def send_acknowledgement_email_on_instance_provisioning(sender, **kwargs):
    """
    Send acknowledgement email for successful instance provisioning, except
    for periodic builds.
    """
    instance = kwargs['instance']
    appserver = kwargs['appserver']
    deployment_id = kwargs['deployment_id']

    if deployment_id is None or appserver is None:
        return

    deployment = Deployment.objects.get(pk=deployment_id)

    # Send emails for only user triggered emails
    # The deployments triggered on DeploymentType.registration are
    # handled and send welcome email to user on success
    if deployment.type != DeploymentType.user.name:
        return

    # The instance should be associate with at most one BetTestApplication
    # by design, thus we can selected the first record.
    application = instance.betatestapplication_set.first()
    is_appserver_healthy = appserver.status.is_healthy_state

    # Send email only for registered client application where application status is
    # accepted. Applications with pending status will go through the approval signal
    # and send welcome email.
    if not application or application.status != BetaTestApplication.ACCEPTED:
        return

    # Send the emails for registered client applications only for healthy AppServer state
    if not is_appserver_healthy:
        return

    send_changes_deployed_success_email(application)
