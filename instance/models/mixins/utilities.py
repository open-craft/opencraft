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

import ast
import re
import logging
import sys
import json
from copy import deepcopy
from typing import Any, List, Dict, Tuple, Optional, Union
from pprint import pformat

import yaml
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
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
        re.compile(r".*jwt(\-|\_)?.*"),
        re.compile(r".*key(\-|\_)?.*"),
        re.compile(r".*pass(w(or)?d)?.*"),
        re.compile(r".*private.*"),
        re.compile(r".*secret.*"),
        re.compile(r".*sensitive.*"),
        re.compile(r".*token(\-|\_)?.*"),
    ]

    SENSITIVE_KEY_PATTERNS: list = COMMON_PATTERNS + []

    SENSITIVE_VALUE_PATTERNS: list = COMMON_PATTERNS + [
        # This will match is extremely broad, but the safest
        re.compile(r"^(?!/).*\w+\:[\w\#\=\_\-\*\!\+\$\@\&\%\^]+"),
    ]

    def __init__(self, data: DataType):
        self.data: SensitiveDataFilter.DataType = deepcopy(data)

    def __mask_data(self, value: DataType) -> Optional[str]:
        """
        Based on the value type, route masking to the corresponding function.
        """
        if isinstance(value, list):
            self.__mask_list_data(value)
        elif isinstance(value, dict):
            self.__mask_dict_value(value)
        elif isinstance(value, str):
            return self.__mask_text(value)

        return None

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
                masked_text = self.__mask_data(value)
                if masked_text:
                    data[key] = masked_text

    def __mask_list_data(self, data: ListDataType):
        """
        Replace the elements of the list based on its type.
        """
        for index, value in enumerate(data):
            masked_text = self.__mask_data(value)
            if masked_text:
                data[index] = masked_text

    def __enter__(self) -> "SensitiveDataFilter.DataType":
        """
        Handle entering the context manager.
        """
        masked_text = self.__mask_data(self.data)
        if masked_text:
            self.data = masked_text

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

def _extract_message_from_ansible_log(match) -> Optional[dict]:
    """
    Extract message match group from ansible log lines.
    """
    if match and match.group('message'):
        try:
            return json.loads(match.group('message'))
        except json.decoder.JSONDecodeError:
            # the message can be an explicitly printed dict which must be parsed
            return ast.literal_eval(match.group('message'))

    return None


def _extract_most_relevant_log(entries, task_name_pattern, relevant_log_pattern) -> Tuple[str, Dict[str, Any]]:
    """
    Make sure we extract most relevant log from the logs to help communities by providing
    meaningful build logs.
    """
    task_name: str = ""
    log_entry: Dict[str, Any] = dict()

    for entry in entries.order_by('-created')[:settings.LOG_LIMIT]:
        if log_entry and task_name:
            break

        text = entry.text.strip()
        task_name_match = task_name_pattern.match(text)
        relevant_log_match = relevant_log_pattern.match(text)

        if task_name_match:
            task_name = task_name_match.group("task")

        if relevant_log_match:
            log_entry = _extract_message_from_ansible_log(relevant_log_match)

    return task_name, log_entry


def _extract_other_build_logs(entries, log_pattern) -> List[str]:
    """
    Make sure we extract other build logs from the provisioning logs, so we can attach more information
    when we send a failure notification email.
    """
    other_ansible_logs: List[str] = list()

    # To get the logs in order, we need to have a separate iteration, which
    # cannot be combined with the previous one. Fortunately, under normal
    # circumstances, the previous iteration will finish pretty fast.
    for entry in entries:
        text = entry.text.strip()
        log_match = log_pattern.match(text)
        extracted_message = _extract_message_from_ansible_log(log_match)

        if not extracted_message:
            continue

        other_ansible_logs.append(extracted_message)

    return other_ansible_logs


def get_ansible_failure_log_entry(entries) -> Tuple[str, Dict[str, Any], List[str]]:
    """
    Get the most relevant failure log entry related to Ansible run and the Ansible
    task name.
    """
    task_name_pattern = re.compile(r".*\|\s+TASK\s\[(?P<task>.*)\].*")
    relevant_log_pattern = re.compile(r".*\|\s+(\w+)\:.*\=\>\s+(\(item\=)?(?P<message>\{.*\})\)?")

    task_name, log_entry = _extract_most_relevant_log(entries, task_name_pattern, relevant_log_pattern)
    other_ansible_logs = _extract_other_build_logs(entries, relevant_log_pattern)

    return task_name, log_entry, other_ansible_logs


def send_periodic_deployment_success_email(recipients: List[str], instance_name: str) -> None:
    """
    Send notification email about successful periodic deployments.

    This email sending should be called, when the previous deployment failed, but the
    latest passed.
    """
    logger.warning(
        "Sending acknowledgement e-mail to %s after instance %s didn provision",
        recipients,
        instance_name,
    )

    send_mail(
        'Deployment back to normal at instance: {}'.format(instance_name),
        'The deployment of a new appserver was successful. You can consider any failure notification '
        'related to {} as resolved. No further action needed.'.format(instance_name),
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )


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


def send_periodic_deployment_failure_email(recipients: List[str], instance) -> None:
    """
    Send notification email about failed periodic deployments.

    The configuration details are retrieved from the app server, because the instance's
    configuration may change between the deployment and sending the email, though the chance
    for this is really small.
    """
    instance_name = str(instance)

    # Get the latest appserver
    appserver = instance.appserver_set.first()

    latest_successful_appserver = max(
        filter(lambda i: i.status.is_healthy_state, instance.appserver_set.all()),
        key=lambda i: i.created,
        default=None
    )

    if latest_successful_appserver:
        latest_deployment_success_date = latest_successful_appserver.log_entries_queryset.last().created
    else:
        latest_deployment_success_date = 'N/A'

    with SensitiveDataFilter(yaml.load(appserver.configuration_settings, Loader=yaml.FullLoader)) as filtered_data:
        filtered_configuration = json.dumps(filtered_data)

    # Reverse the log entries to start looking for failure from the latest log entry
    ansible_task_name, raw_ansible_log_entry, other_raw_logs = get_ansible_failure_log_entry(
        appserver.log_entries_queryset
    )

    with SensitiveDataFilter(raw_ansible_log_entry) as filtered_data:
        relevant_log_entry = pformat(filtered_data)

    with SensitiveDataFilter(other_raw_logs) as filtered_data:
        other_log_entries = json.dumps(filtered_data)

    logger.warning(
        "Sending notification e-mail to %s after instance %s didn't provision",
        recipients,
        instance_name,
    )

    email = EmailMultiAlternatives(
        'Deployment failed at instance: {}'.format(instance_name),
        'The periodic deployment of {edx_platform_release} failed. Please see the details below.\n\n'
        'Ansible task name:\t{ansible_task_name}\n'
        'Relevant log lines:\n{relevant_log_entry}\n\n'
        'AppServer ID:\t{appserver_id}\n'
        'Latest successful provision date: {latest_successful_provision_date}\n'
        'Configuration source repo:\t{configuration_source_repo_url}\n'
        'Configuration version:\t{configuration_version}\n'
        'OpenEdX platform source repo:\t{edx_platform_repository_url}\n'
        'OpenEdX platform release:\t{edx_platform_release}\n'
        'OpenEdX platform commit:\t{edx_platform_commit}'.format(
            ansible_task_name=ansible_task_name,
            appserver_id=appserver.id,
            configuration_source_repo_url=appserver.configuration_source_repo_url,
            configuration_version=appserver.configuration_version,
            edx_platform_commit=appserver.edx_platform_commit,
            edx_platform_release=appserver.openedx_release,
            edx_platform_repository_url=appserver.edx_platform_repository_url,
            latest_successful_provision_date=str(latest_deployment_success_date),
            relevant_log_entry=relevant_log_entry,
        ),
        settings.DEFAULT_FROM_EMAIL,
        recipients
    )

    # Attach logs and configuration settings as attachments to keep the email readable
    email.attachments.append(("build_log.json", other_log_entries, "application/json"))
    email.attachments.append(("configuration.json", filtered_configuration, "application/json"))

    email.send()


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
                instance
            )


@receiver(appserver_spawned)
def send_acknowledgement_email_on_deployment_success(sender, **kwargs) -> None:
    """
    Send acknowledge emails for successful, but previously failed, periodic builds
    where community is waiting for deployment notifications.
    """
    instance = kwargs['instance']
    appserver = kwargs['appserver']
    deployment_id = kwargs['deployment_id']

    if deployment_id is None or appserver is None:
        return

    deployment = Deployment.objects.get(pk=deployment_id)
    if deployment.type != DeploymentType.periodic.name:
        return

    is_appserver_healthy = appserver.status.is_healthy_state
    is_periodic_builds_enabled = instance.periodic_builds_enabled
    periodic_build_failure_emails = instance.periodic_build_failure_notification_emails

    if not is_appserver_healthy or not is_periodic_builds_enabled or not periodic_build_failure_emails:
        return

    try:
        previous_appserver = appserver.get_previous_by_created()
    except ObjectDoesNotExist:  # Not using the strict exception to not cause circular dependencies
        previous_appserver = None

    if previous_appserver is None or previous_appserver.status.is_healthy_state:
        return

    send_periodic_deployment_success_email(
        periodic_build_failure_emails,
        str(instance)
    )
