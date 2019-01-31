# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <xavier@opencraft.com>
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
from django.core.mail import EmailMessage
from django.dispatch import receiver
from django.template.loader import get_template

from registration.models import BetaTestApplication
from instance.models.appserver import AppServer
from instance.signals import appserver_spawned


# Functions ###################################################################

def _send_mail(application, template_name, subject):
    """Helper function to send an email to the user."""
    template = get_template(template_name)
    message = template.render(dict(
        application=application,
        signature=settings.BETATEST_EMAIL_SIGNATURE,
    ))
    EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.BETATEST_EMAIL_SENDER,
        to=(application.user.email,),
        bcc=(settings.BETATEST_EMAIL_INTERNAL,)
    ).send()


def accept_application(application, appserver):
    """Accept a beta test application.

    This helper function verifies that an AppServer for this application has been successfully
    launched, activates it and sends an email to the user to notify them that their instance is
    ready.
    """
    instance = application.instance
    if instance is None:
        raise ApplicationNotReady('No instance provisioned yet.')

    if appserver is None:
        raise ApplicationNotReady('The instance does not have an active AppServer yet.')
    if appserver.status != AppServer.Status.Running:
        raise ApplicationNotReady('The AppServer is not running yet.')

    # Automatically activates AppServer if it's the first one from the instance
    if not instance.first_activated:
        appserver.make_active()

    _send_mail(application, 'registration/welcome_email.txt', settings.BETATEST_WELCOME_SUBJECT)
    application.status = BetaTestApplication.ACCEPTED
    application.save()


@receiver(appserver_spawned)
def on_appserver_spawned(sender, **kwargs):
    """
    Monitor spawning of new appservers, to send the welcome email once it is ready.
    """
    instance = kwargs['instance']
    appserver = kwargs['appserver']
    application = instance.betatestapplication_set.first()  # There should only be one

    if not application or application.status != BetaTestApplication.PENDING:
        return

    elif appserver is None:
        raise ApplicationNotReady('Provisioning of AppServer failed.')

    else:
        accept_application(application, appserver)


# Exceptions ##################################################################

class ApplicationNotReady(Exception):
    """
    Raised when trying to process an application which isn't ready yet
    """
    pass
