# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
Send notification emails when certain deployment events happen.
"""

import traceback

from functools import wraps
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template

def send_emails_on_deployment_failure(method):
    """
    Decorator around spawn_appserver that catches all the emited exceptions and notifies by email
    when it detects that a server deployment failed because of infrastructure problems.
    It doesn't change spawn_server's behaviour (it will still raise exceptions on error).
    It is done as a decorator to separate the e-mail code from the server-spawning code.

    Different instances might have different e-mail requirements. E.g. an instance that builds the 'master'
    branch of edx/edx-platform will send an e-mail to edX devops in case of failure.
    In a future version, we could detect the 'owner' of the instance (e.g. the person who created the PR) and notify
    them by e-mail when a deployment finished with or without error.
    """
    @wraps(method)
    def wrapper(self, *args, **kwds): #pylint: disable=missing-docstring

        try:
            result = method(self, *args, **kwds)
        except Exception as e:
            # This means that the deployment failed due to infrastructure problems (which raise exceptions), e.g.
            # OVH down, or an incorrect MySQL/MongoDB login/password, etc.
            # Notify OpenCraft
            if settings.INFRASTRUCTURE_DEPLOYMENT_PROBLEMS_EMAIL:
                stacktrace = traceback.format_exc()
                context = {
                    'instance': self,
                    'exception': e,
                    'exception_type': e.__class__.__name__,
                    'stacktrace': stacktrace,
                }
                subject = get_template('instance/emails/infrastructure_deployment_error_subject.txt').render(context)
                subject = ''.join(subject.splitlines())
                text = get_template('instance/emails/infrastructure_deployment_error_body.txt').render(context)
                sender = settings.DEFAULT_FROM_EMAIL
                dest = [settings.INFRASTRUCTURE_DEPLOYMENT_PROBLEMS_EMAIL]
                send_mail(subject, text, sender, dest)

            raise

        if not result:
            # This means that the deployment failed not due to infrastructure problems (which raise exceptions) but
            # due to the Open edX ansible playbook not finishing correctly.
            # Notify OpenCraft, and in the case of building edx/edx-platform's master notify upstream too

            # One of our instances is for CI of edx/edx-platform and a failure on it must send e-mail to upstream devops
            is_upstream_edx_build = self.internal_lms_domain.startswith('master.') and \
                self.name.startswith('Integration') and \
                'edx/edx-platform' in self.edx_platform_repository_url and \
                self.edx_platform_commit == 'master'

            if settings.OPENEDX_DEPLOYMENT_PROBLEMS_EMAIL:
                context = { 'instance': self }
                subject = get_template('instance/emails/openedx_deployment_error_subject.txt').render(context)
                subject = ''.join(subject.splitlines())
                text = get_template('instance/emails/openedx_deployment_error_body.txt').render(context)
                sender = settings.DEFAULT_FROM_EMAIL
                dest = [settings.OPENEDX_DEPLOYMENT_PROBLEMS_EMAIL]
                if is_upstream_edx_build and settings.INFRASTRUCTURE_DEPLOYMENT_PROBLEMS_EMAIL:
                    dest.append(settings.INFRASTRUCTURE_DEPLOYMENT_PROBLEMS_EMAIL)

                send_mail(subject, text, sender, dest)

        return result

    return wrapper
