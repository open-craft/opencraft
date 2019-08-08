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
Open edX instance monitoring mixin
"""

# Imports #####################################################################

from django.conf import settings
from django.db import models
from django.db.models import ProtectedError

from instance import newrelic


# Classes #####################################################################

class OpenEdXMonitoringMixin:
    """
    Mixin that sets up availability monitoring for Open edX instances.
    """
    def enable_monitoring(self):
        """
        Enable monitoring on this instance.
        """
        if not settings.NEWRELIC_ADMIN_USER_API_KEY:
            self.logger.warning('Skipping monitoring setup, '
                                'NEWRELIC_ADMIN_USER_API_KEY not set')
            return
        self.logger.info('Checking New Relic Synthetics monitors')

        # The notifications for the monitors are now set up using New Relic alert policies. Alert policies
        # can contain one or more alert conditions and an alert condition can be associated with
        # one or more Synthetics (aka availability) monitors.
        #
        # An alert policy can have one or more existing notification channels added to it. We use email
        # notification channels for sending out email notifications.
        #
        # The alert policy can be configured to create an incident per policy, per alert condition or per monitor and
        # entity (for each failure). We use the 'per-policy' setting on all the alert policies.

        if not hasattr(self, 'new_relic_alert_policy'):
            alert_policy_id = newrelic.add_alert_policy(self.domain)
            NewRelicAlertPolicy.objects.create(id=alert_policy_id, instance=self)

        urls_to_monitor = self._urls_to_monitor  # Store locally so we don't keep re-computing this
        already_monitored_urls = set()

        for monitor in self.new_relic_availability_monitors.all():
            url = newrelic.get_synthetics_monitor(monitor.pk)['uri']
            if url in urls_to_monitor:
                already_monitored_urls.add(url)
            else:
                self.logger.info('Deleting New Relic Synthetics monitor for old public URL %s', url)
                monitor.delete()

        for url in urls_to_monitor - already_monitored_urls:
            self.logger.info('Creating New Relic Synthetics monitor for new public URL %s', url)
            new_monitor_id = newrelic.create_synthetics_monitor(url)
            monitor = self.new_relic_availability_monitors.create(pk=new_monitor_id)
            alert_condition_id = newrelic.add_alert_condition(self.new_relic_alert_policy.id, new_monitor_id, url)
            monitor.new_relic_alert_conditions.create(id=alert_condition_id, alert_policy=self.new_relic_alert_policy)

        # Set up email alerts.
        # We add emails here but never remove them - that must be done manually (or the monitor deleted)
        # in order to reduce the chance of bugs or misconfigurations accidentally suppressing monitors.
        emails_to_monitor = set([email for name, email in settings.ADMINS] + self.additional_monitoring_emails)
        if emails_to_monitor:
            emails_current = set(
                self.new_relic_alert_policy.email_notification_channels.values_list('email', flat=True)
            )
            emails_to_add = list(emails_to_monitor - emails_current)
            if emails_to_add:
                self.logger.info(
                    'Adding email(s) to policy %s: %s', self.new_relic_alert_policy.id, ', '.join(emails_to_add)
                )
                self._add_emails(emails_to_add)

    def _add_emails(self, emails):
        """
        Create a notification channel for each given email address if it doesn't exist and add it to this instance's
        alert policy.
        """
        channel_ids = []
        for email in emails:
            try:
                channel = NewRelicEmailNotificationChannel.objects.get(email=email)
                self.logger.info(
                    'Email notification channel for {} already exists. Using it.'.format(email)
                )
                channel_id = channel.id
            except NewRelicEmailNotificationChannel.DoesNotExist:
                self.logger.info('Creating a new email notification channel for {}'.format(email))
                channel_id = newrelic.add_email_notification_channel(email)
                channel = NewRelicEmailNotificationChannel.objects.create(id=channel_id, email=email)
                self.new_relic_alert_policy.email_notification_channels.add(channel)
            channel_ids.append(channel_id)
        # Always add all the notification channels corresponding to the given emails to the policy.
        # Existing email notification channels are ignored.
        newrelic.add_notification_channels_to_policy(self.new_relic_alert_policy.id, sorted(channel_ids))

    def disable_monitoring(self):
        """
        Disable monitoring on this instance.
        """
        self.logger.info('Removing New Relic Synthetics monitors')
        for monitor in self.new_relic_availability_monitors.all():
            monitor.delete()

        if hasattr(self, 'new_relic_alert_policy'):
            for channel in self.new_relic_alert_policy.email_notification_channels.filter(shared=False):
                channel.delete()
            NewRelicAlertPolicy.objects.get(instance=self).delete()

    @property
    def _urls_to_monitor(self):
        """
        The urls to monitor for this instance.
        """
        return {self.url, self.studio_url, self.lms_preview_url, self.lms_extended_heartbeat_url}


class NewRelicAvailabilityMonitor(models.Model):
    """
    A New Relic Synthetics availability monitor for an instance.
    """
    id = models.CharField(max_length=256, primary_key=True)
    instance = models.ForeignKey(
        'OpenEdXInstance', related_name='new_relic_availability_monitors', on_delete=models.CASCADE
    )

    def __str__(self):
        return self.pk

    def delete(self, *args, **kwargs):
        """
        Disable this availability monitor on delete.
        """
        newrelic.delete_synthetics_monitor(self.pk)
        super().delete(*args, **kwargs)


class NewRelicAlertPolicy(models.Model):
    """
    A New Relic alert policy for an instance.
    """
    id = models.IntegerField(primary_key=True)
    instance = models.OneToOneField(
        'OpenEdXInstance', related_name='new_relic_alert_policy', on_delete=models.CASCADE
    )
    email_notification_channels = models.ManyToManyField(
        'NewRelicEmailNotificationChannel', related_name='new_relic_alert_policies'
    )

    def __str__(self):
        return self.pk

    def delete(self, *args, **kwargs):
        """
        Delete this alert policy.
        """
        newrelic.delete_alert_policy(self.id)
        super().delete(*args, **kwargs)


class NewRelicEmailNotificationChannel(models.Model):
    """
    A New Relic notification channel.
    """
    id = models.IntegerField(primary_key=True)
    email = models.EmailField(unique=True)
    shared = models.BooleanField(default=False)

    def __str__(self):
        return self.pk

    def delete(self, *args, **kwargs):
        """
        Delete this email notification channel.
        """
        if not self.shared:
            newrelic.delete_email_notification_channel(self.id)
            super().delete(*args, **kwargs)
        else:
            raise ProtectedError('Cannot delete a shared email notification channel', self)


class NewRelicAlertCondition(models.Model):
    """
    A New Relic alert condition for an instance under an alert policy
    """
    id = models.IntegerField(primary_key=True)
    monitor = models.ForeignKey(
        'NewRelicAvailabilityMonitor', related_name='new_relic_alert_conditions', on_delete=models.CASCADE
    )
    alert_policy = models.ForeignKey(
        'NewRelicAlertPolicy', related_name='new_relic_alert_conditions', on_delete=models.CASCADE
    )

    def __str__(self):
        return self.pk
