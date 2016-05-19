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
"""Helper functions for approving or rejecting beta test applications.

These functions are meant to be used manually from the interactive Python shell.
"""

# Imports #####################################################################

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template

from registration.models import BetaTestApplication

# Settings ####################################################################

BETATEST_EMAIL_SENDER = getattr(settings, 'BETATEST_EMAIL_SENDER', settings.DEFAULT_FROM_EMAIL)
BETATEST_WELCOME_SUBJECT = getattr(
    settings,
    'BETATEST_WELCOME_SUBJECT',
    'Welcome to the OpenCraft Instance Manager beta test!',
)
BETATEST_REJECT_SUBJECT = getattr(
    settings,
    'BETATEST_REJECT_SUBJECT',
    'An update on your beta test application status for OpenCraft Instance Manager',
)

# Functions ###################################################################


def accept_application(application):
    """Accept a beta test application.

    This helper function verifies that an AppServer for this application has been successfully
    launched, activates it and sends an email to the user to notify them that their instance is
    ready.
    """
    assert application.instance is not None, 'No instance provisioned yet.'
    appserver = application.instance.active_appserver
    assert appserver is not None, 'The instance does not have an active AppServer yet.'
    assert appserver.status == appserver.Status.Running, 'The AppServer is not running yet.'
    message = get_template('registration/welcome_email.txt').render({'application': application})
    send_mail(
        subject=BETATEST_WELCOME_SUBJECT,
        message=message,
        from_email=BETATEST_EMAIL_SENDER,
        recipient_list=(application.user.email,),
    )
    application.status = BetaTestApplication.ACCEPTED
    application.save()


def reject_application(application):
    """Reject a beta test application.

    All servers associated with the application will be terminated, and an email is send to the
    applicant to inform them that the application has been rejected.
    """
    if application.instance is not None:
        for appserver in application.instance.appserver_set.iterator():
            appserver.terminate_vm()
    message = get_template('registration/reject_email.txt').render({'application': application})
    send_mail(
        subject=BETATEST_REJECT_SUBJECT,
        message=message,
        from_email=BETATEST_EMAIL_SENDER,
        recipient_list=(application.user.email,),
    )
    application.status = BetaTestApplication.REJECTED
    application.save()
