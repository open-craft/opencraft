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
Utility function related to registration.
"""

from simple_email_confirmation.models import EmailAddress

from email_verification import send_email_verification


def verify_user_emails(user, request, *email_addresses):
    """
    Start email verification process for specified email addresses.

    This should ignore already-verified email addresses.
    """
    for email_address in email_addresses:
        if not EmailAddress.objects.filter(email=email_address).exists():
            email = EmailAddress.objects.create_unconfirmed(email_address, user)
            send_email_verification(email, request)
