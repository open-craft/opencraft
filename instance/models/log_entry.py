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
Instance app models - LogEntry
"""

# Imports #####################################################################

import logging

from django.db import models
from django_extensions.db.models import TimeStampedModel

from instance.models.instance import OpenEdXInstance
from instance.models.server import OpenStackServer
from instance.models.utils import ValidateModelMixin


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Models ######################################################################

class LogEntry(ValidateModelMixin, TimeStampedModel):
    """
    Single log entry
    """
    LOG_LEVEL_CHOICES = (
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    )

    text = models.TextField(blank=True)
    level = models.CharField(max_length=9, db_index=True, default='info', choices=LOG_LEVEL_CHOICES)

    class Meta:
        abstract = True
        permissions = (
            ("read_log_entry", "Can read LogEntry"),
        )

    def __str__(self):
        return '{0.created:%Y-%m-%d %H:%M:%S} | {0.level:>8s} | {0.text}'.format(self)


class GeneralLogEntry(LogEntry):
    """
    Single log entry that isn't attached to a specific model, such as instances or servers
    """
    class Meta:
        verbose_name_plural = "General Log Entries"


class InstanceLogEntry(LogEntry):
    """
    Single log entry for instances
    """
    obj = models.ForeignKey(OpenEdXInstance, related_name='log_entry_set')

    class Meta:
        verbose_name_plural = "Instance Log Entries"


class ServerLogEntry(LogEntry):
    """
    Single log entry for servers
    """
    obj = models.ForeignKey(OpenStackServer, related_name='log_entry_set')

    class Meta:
        verbose_name_plural = "Server Log Entries"
