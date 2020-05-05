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

from opencraft.utils import html_email_helper


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
