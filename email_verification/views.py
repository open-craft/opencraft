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
Views for email verification
"""

# Imports #####################################################################

from django.http import Http404
from django.shortcuts import render

from simple_email_confirmation.exceptions import EmailConfirmationExpired
from simple_email_confirmation.models import EmailAddress


# Views #######################################################################

def verify_email(request, code):
    """
    Verify the given email address, and display a message to the user.
    """
    try:
        email = EmailAddress.objects.confirm(code).email
    except EmailAddress.DoesNotExist:
        raise Http404
    except EmailConfirmationExpired:
        email = None
        expired = True
    else:
        expired = False
    return render(request, 'email_verification/verify.html', context={
        'email': email,
        'expired': expired,
    })
