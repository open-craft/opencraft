# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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

# Imports #####################################################################

import re
import logging
import sys
import json
from copy import deepcopy
from typing import Any, List, Dict, Tuple, Optional, Union

from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.core.mail import send_mail
from django.dispatch import receiver
from django.views.debug import ExceptionReporter

from instance.models.deployment import Deployment, DeploymentType
from instance.signals import appserver_spawned

logger = logging.getLogger(__name__)

# Classes #####################################################################


class SensitiveDataFilter:
    """
    Filter and hide sensitive data in config and logs.
    """

    DictDataType = Dict[str, Any]
    ListDataType = Union[List[str], List[Dict[str, Any]]]
    DataType = Union[str, DictDataType, ListDataType]

    FILTERED_TEXT = "[Filtered data]"

    COMMON_PATTERNS: list = [
        re.compile(r".*api(\-|\_)?.*"),
        re.compile(r".*key(\-|\_)?.*"),
        re.compile(r".*token(\-|\_)?.*"),
    ]

    SENSITIVE_KEY_PATTERNS: list = COMMON_PATTERNS + [
        re.compile(r".*pass(w(or)?d)?.*"),
        re.compile(r".*secret.*"),
        re.compile(r".*private.*"),
        re.compile(r".*sensitive.*"),
    ]

    SENSITIVE_VALUE_PATTERNS: list = COMMON_PATTERNS + [
        re.compile(r".*\:.*"),
    ]

    def __init__(self, data: DataType):
        self.data: SensitiveDataFilter.DataType = deepcopy(data)

    def __mask_data(self, index: Optional[Union[int, str]], value: DataType) -> None:
        """
        Based on the value type, route masking to the corresponding function.
        """
        if isinstance(value, list):
            self.__mask_list_data(value)
        elif isinstance(value, dict):
            self.__mask_dict_value(value)

    def __mask_text(self, text: str) -> str:
        """
        Replace text with the masked value if sensitive data found.
        """
        lowered_text = text.lower()
        if any([p.match(lowered_text) for p in self.SENSITIVE_VALUE_PATTERNS]):
            return self.FILTERED_TEXT

        return text

    def __mask_dict_value(self, data: DictDataType) -> None:
        """
        Replace the value of the dictionary, if the key seems to contain
        sensitive data.
        """
        for key, value in data.items():
            matching_key = any([p.match(key.lower()) for p in self.SENSITIVE_KEY_PATTERNS])
            if matching_key and isinstance(value, str):
                data[key] = self.FILTERED_TEXT
            else:
                self.__mask_data(key, value)

    def __mask_list_data(self, data: ListDataType):
        """
        Replace the elements of the list based on its type.
        """
        for index, item in enumerate(data):
            if isinstance(item, str):
                data[index] = self.__mask_text(item)
            else:
                self.__mask_data(index, item)

    def __enter__(self) -> "SensitiveDataFilter.DataType":
        """
        Handle entering the context manager.
        """
        if isinstance(self.data, str):
            self.data = self.__mask_text(self.data)
        else:
            self.__mask_data(None, self.data)

        return self.data

    def __exit__(self, *args, **kwargs) -> None:
        return


class EmailMixin:
    """
    Mixin that enables AppServer to send emails
    """
    class EmailSubject:
        """
        Class holding email subject constants
        """
        PROVISION_FAILED = "AppServer {name} ({instance_name}) failed to provision"

    class EmailBody:
        """
        Class holding email body constants
        """
        PROVISION_FAILED = "AppServer {name} for Instance {instance_name} failed to provision.\n" \
                           "Reason: {reason}\n"

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
        Send email notifications after a server's provisioning has failed.
        This will happen once for each deployment attempt if there are many.
        It will send notifications to settings.ADMINS.
        """
        attachments = []
        if log is not None:
            log_str = "\n".join(log)
            attachments.append(("provision.log", log_str, "text/plain"))

        self._send_email(
            self.EmailSubject.PROVISION_FAILED.format(name=self.name, instance_name=self.instance.name),
            self.EmailBody.PROVISION_FAILED.format(name=self.name, instance_name=self.instance.name, reason=reason),
            self._get_exc_info(default=None),
            attachments=attachments,
            extra_recipients=[],
        )

    def _send_email(self, subject, message, exc_info=None, attachments=None,
                    extra_recipients: Optional[List[str]] = None):
        """
        Helper method mimicking :class:`AdminEmailHandler` - if exception is available renders traceback as HTML message
        content
        """
        if exc_info is not None:
            reporter = ExceptionReporter(None, is_email=True, *exc_info)
            html_message = reporter.get_traceback_html()
            attachments.append(("debug.html", html_message, "text/html"))

        self.logger.info("Sending message to admins: %s - %s", subject, message)
        self._mail_admins_with_attachment(subject, message, attachments=attachments, extra_recipients=extra_recipients)

    @staticmethod
    def _mail_admins_with_attachment(
            subject,
            message,
            fail_silently=True,
            connection=None,
            html_message=None,
            attachments=None,
            extra_recipients: Optional[List[str]] = None,
    ):
        """
        Mimics mail_admins, but allows attaching files to the message
        """
        if not settings.ADMINS and not extra_recipients:
            return

        recipients = [a[1] for a in settings.ADMINS] + extra_recipients
        mail = EmailMultiAlternatives(
            "%s%s" % (settings.EMAIL_SUBJECT_PREFIX, subject),
            message, settings.SERVER_EMAIL, recipients,
            connection=connection
        )

        if html_message:
            mail.attach_alternative(html_message, "text/html")

        if attachments:
            for attachment_name, attachment_content, attachment_mime in attachments:
                mail.attach(attachment_name, attachment_content, attachment_mime)

        mail.send(fail_silently=fail_silently)


# Functions #####################################################################

def get_ansible_failure_log_entry(entries) -> Tuple[str, Dict[str, Any]]:
    """
    Get the most relevant failure log entry related to Ansible run and the Ansible
    task name.
    """
    task_name_pattern = re.compile(r"^TASK\s\[(?P<task>.*)\]")
    relevant_log_pattern = re.compile(r"^(fatal|critical)\:.*\=\>\s+")

    task_name: str = ""
    log_entry: Dict[str, Any] = dict()

    for entry in entries.order_by('-created')[:settings.LOG_LIMIT]:
        if log_entry and task_name:
            break

        text = entry.text.split("|")[-1].strip()
        task_name_match = task_name_pattern.match(text)

        if task_name_match:
            task_name = task_name_match.group("task")

        if relevant_log_pattern.match(text):
            log_entry = json.loads(relevant_log_pattern.sub("", text).strip())


    return (task_name, log_entry)


def send_urgent_deployment_failure_email(recipients: List[str], instance_name: str) -> None:
    """
    Send urgent notification email about failed deployments.
    """
    logger.warning(
        "Sending urgent alert e-mail to %s after instance %s didn't provision",
        recipients,
        instance_name,
    )

    send_mail(
        'Deployment failed at instance: {}'.format(instance_name),
        'The deployment of a new appserver failed and needs manual intervention. '
        'You can find the logs in the web interface.',
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )


def send_periodic_deployment_failure_email(recipients: List[str], instance_name: str, openedx_release: str) -> None:
    """
    Send notification email about failed periodic deployments.
    """
    logger.warning(
        "Sending notification e-mail to %s after instance %s didn't provision",
        recipients,
        instance_name,
    )

    send_mail(
        'Deployment failed at instance: {}'.format(instance_name),
        'The periodic deployment of {} failed. '
        'You can find the logs in the web interface.'.format(openedx_release),
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )


@receiver(appserver_spawned)
def send_urgent_alert_on_permanent_deployment_failure(sender, **kwargs) -> None:
    """
    Send an urgent alert to an e-mail when the deployment fails in a way that blocks the user.
    This is more urgent than the usual failure e-mails, and it's meant to go for instance to PagerDuty.
    This alert will only happen after ALL deployment attempts have been consumed, and ONLY if the deployment
    was triggered by the user (i.e. if the admins mass-redeploy 100 instances and 3 of them fail, this isn't
    critical and it doesn't trigger this e-mail)..
    """
    instance = kwargs['instance']
    appserver = kwargs['appserver']
    deployment_id: int = kwargs['deployment_id']

    # Those deployment types which are triggered by OpenCraft members
    ignorable_deployment_types: List[str] = [
        DeploymentType.admin.name,
        DeploymentType.batch.name,
        DeploymentType.pr.name
    ]

    is_registered_by_client = instance.betatestapplication_set.exists()
    is_periodic_builds_enabled = instance.periodic_builds_enabled

    # Only sending critical alerts for failures in registered clients' instances, not in test/sandboxes
    # except for periodic builds
    if not is_registered_by_client and not is_periodic_builds_enabled:
        return

    # In case a deployment initiated by an OpenCraft member
    # and failed, skip sending urgent email
    if deployment_id is not None:
        deployment = Deployment.objects.get(pk=deployment_id)
        if deployment.type in ignorable_deployment_types:
            logger.warning(
                'Skip sending urgent alert e-mail after instance %s '
                'provisioning failed since it was initiated by OpenCraft member',
                instance,
            )
            return

    if appserver is None:
        provisioning_failure_emails = instance.provisioning_failure_notification_emails
        periodic_build_failure_emails = instance.periodic_build_failure_notification_emails

        if is_registered_by_client and provisioning_failure_emails:
            send_urgent_deployment_failure_email(
                provisioning_failure_emails,
                str(instance)
            )

        if is_periodic_builds_enabled and periodic_build_failure_emails:
            send_periodic_deployment_failure_email(
                periodic_build_failure_emails,
                str(instance),
                instance.openedx_release
            )
