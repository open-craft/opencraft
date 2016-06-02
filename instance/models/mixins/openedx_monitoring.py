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
            return

        # Delete existing monitors if they don't monitor this instance's
        # public urls
        monitors = newrelic.get_synthetics_monitors()
        already_enabled = [monitor for monitor in monitors
                           if monitor['uri'] in self._urls_to_monitor]
        already_enabled_ids = {enabled['id'] for enabled in already_enabled}
        for monitor in self.new_relic_availability_monitors.exclude(
                pk__in=already_enabled_ids):
            monitor.delete()

        # Add monitors for urls that are not already being monitored
        already_enabled_urls = {enabled['uri'] for enabled in already_enabled}
        for url in self._urls_to_monitor - already_enabled_urls:
            monitor_id = newrelic.create_synthetics_monitor(url)
            self.new_relic_availability_monitors.create(pk=monitor_id)

            # Set up email alerts
            if settings.ADMINS:
                emails = [email for name, email in settings.ADMINS]
                newrelic.add_synthetics_email_alerts(monitor_id, emails)

    def disable_monitoring(self):
        """
        Disable monitoring on this instance.
        """
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
    id = models.CharField(max_length=256, primary_key=True)
    instance = models.ForeignKey('OpenEdXInstance', related_name='new_relic_availability_monitors')

    def __str__(self):
        return self.pk

    def delete(self, *args, **kwargs):
        """
        Disable this availability monitor on delete.
        """
        newrelic.delete_synthetics_monitor(self.pk)
        super().delete(*args, **kwargs)  # pylint: disable=no-member
