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
from instance.models.appserver import AppServer

# Settings ####################################################################

BETATEST_WELCOME_SUBJECT = 'Welcome to the OpenCraft Instance Manager free 30-day trial!'
BETATEST_REJECT_SUBJECT = 'An update on your free 30-day trial test application status for OpenCraft Instance Manager'

# Functions ###################################################################


def _send_mail(application, template_name, subject):
    """Helper function to send an email to the user."""
    template = get_template(template_name)
    message = template.render(dict(
        application=application,
        signature=settings.BETATEST_EMAIL_SIGNATURE,
    ))
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.BETATEST_EMAIL_SENDER,
        recipient_list=(application.user.email,),
    )


def accept_application(application):
    """Accept a beta test application.

    This helper function verifies that an AppServer for this application has been successfully
    launched, activates it and sends an email to the user to notify them that their instance is
    ready.
    """
    assert application.instance is not None, 'No instance provisioned yet.'
    appserver = application.instance.active_appserver
    assert appserver is not None, 'The instance does not have an active AppServer yet.'
    assert appserver.status == AppServer.Status.Running, 'The AppServer is not running yet.'
    _send_mail(application, 'registration/welcome_email.txt', BETATEST_WELCOME_SUBJECT)
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
    _send_mail(application, 'registration/reject_email.txt', BETATEST_REJECT_SUBJECT)
    application.status = BetaTestApplication.REJECTED
    application.save()
