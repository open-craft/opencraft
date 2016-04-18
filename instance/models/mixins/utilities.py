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
"""
Instance app model mixins - Utilities
"""
import sys

from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.views.debug import ExceptionReporter


class EmailInstanceMixin(object):
    """
    An instance class that can send emails
    """
    class EmailSubject(object):
        """
        Class holding email subject constants
        """
        PROVISION_FAILED = u"Instance {instance_name} ({instance_url}) failed to provision"

    class EmailBody(object):
        """
        Class holding email body constants
        """
        PROVISION_FAILED = u"Instance {instance_name} failed to provision.\n" \
                           u"Reason: {reason}\n"

    @staticmethod
    def _get_exc_info(default=None):
        """
        Gets exception info if called from exception handler
        """
        exc_info = sys.exc_info()
        # If no exception is being handled anywhere on the stack, a (None, None, None) is returned by exc_info
        if exc_info[0] is None and exc_info[1] is None and exc_info[2] is None:
            return default
        else:
            return exc_info

    def provision_failed_email(self, reason, log=None):
        """
        Send email notifications when instance provisioning is failed
        """
        attachments = []
        if log is not None:
            log_str = "\n".join(log)
            attachments.append(("provision.log", log_str, "text/plain"))

        self._send_email(
            self.EmailSubject.PROVISION_FAILED.format(instance_name=self.name, instance_url=self.url),
            self.EmailBody.PROVISION_FAILED.format(instance_name=self.name, reason=reason),
            self._get_exc_info(default=None),
            attachments=attachments
        )

    def _send_email(self, subject, message, exc_info=None, attachments=None):
        """
        Helper method mimicking :class:`AdminEmailHandler` - if exception is available renders traceback as HTML message
        content
        """
        if exc_info is not None:
            reporter = ExceptionReporter(None, is_email=True, *exc_info)
            html_message = reporter.get_traceback_html()
            attachments.append(("debug.html", html_message, "text/html"))

        self.logger.info("Sending message to admins: %s - %s", subject, message)
        self._mail_admins_with_attachment(subject, message, attachments=attachments)

    @staticmethod
    def _mail_admins_with_attachment(subject, message,
                                     fail_silently=True, connection=None, html_message=None, attachments=None):
        """ Mimics mail_admins, but allows attaching files to the message"""
        if not settings.ADMINS:
            return

        mail = EmailMultiAlternatives(
            "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
            message, settings.SERVER_EMAIL, [a[1] for a in settings.ADMINS],
            connection=connection
        )

        if html_message:
            mail.attach_alternative(html_message, "text/html")

        if attachments:
            for attachment_name, attachment_content, attachment_mime in attachments:
                mail.attach(attachment_name, attachment_content, attachment_mime)

        mail.send(fail_silently=fail_silently)
