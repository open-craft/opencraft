# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <xavier@opencraft.com>
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
            self.new_relic_availability_monitors.create(pk=new_monitor_id)

        # Set up email alerts.
        # We add emails here but never remove them - that must be done manually (or the monitor deleted)
        # in order to reduce the chance of bugs or misconfigurations accidentally supressing monitors.
        emails_to_monitor = set([email for name, email in settings.ADMINS] + self.additional_monitoring_emails)
        if emails_to_monitor:
            for monitor in self.new_relic_availability_monitors.all():
                emails_current = set(newrelic.get_synthetics_notification_emails(monitor.id))
                emails_to_add = list(emails_to_monitor - emails_current)
                if emails_to_add:
                    self.logger.info('Adding email(s) to monitor %s: %s', monitor.id, ', '.join(emails_to_add))
                    newrelic.add_synthetics_email_alerts(monitor.id, emails_to_add)

    def disable_monitoring(self):
        """
        Disable monitoring on this instance.
        """
        self.logger.info('Removing New Relic Synthetics monitors')
        for monitor in self.new_relic_availability_monitors.all():
            monitor.delete()

    @property
    def _urls_to_monitor(self):
        """
        The urls to monitor for this instance.
        """
        return {self.url, self.studio_url, self.lms_preview_url}


class NewRelicAvailabilityMonitor(models.Model):
    """
    A New Relic Synthetics availability monitor for an instance.
    """
    id = models.CharField(max_length=256, primary_key=True)  # pylint: disable=invalid-name
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
