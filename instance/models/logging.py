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
Instance app models - Logging
"""

# Imports #####################################################################

import logging

from swampdragon.pubsub_providers.data_publisher import publish_data

from django.db import models
from django.db.models import query
from django_extensions.db.models import TimeStampedModel

from instance.models.logging_mixin import PUBLISHED_LOG_LEVEL_SET
from instance.models.instance import OpenEdXInstance
from instance.models.server import OpenStackServer
from instance.models.utils import ValidateModelMixin


# Constants ###################################################################

LOG_LEVEL_CHOICES = (
    ('debug', 'Debug'),
    ('info', 'Info'),
    ('warn', 'Warning'),
    ('error', 'Error'),
    ('exception', 'Exception'),
)


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Models ######################################################################

class LogEntryQuerySet(query.QuerySet):
    """
    Additional methods for LogEntry querysets
    Also used as the standard manager for the model (`LogEntry.objects`)
    """
    def create(self, publish=True, *args, **kwargs):
        log_entry = super().create(*args, **kwargs)
        if publish:
            log_entry.publish()


class LogEntry(ValidateModelMixin, TimeStampedModel):
    """
    Single log entry
    """
    text = models.TextField()
    level = models.CharField(max_length=9, db_index=True, default='info', choices=LOG_LEVEL_CHOICES)

    objects = LogEntryQuerySet().as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        return '{0.created:%Y-%m-%d %H:%M:%S} [{0.level}] {0.text}'.format(self)

    @property
    def level_integer(self):
        """
        Integer code for the log entry level
        """
        if self.level == 'exception':
            return logging.__dict__['CRITICAL']
        else:
            return logging.__dict__[self.level.upper()]

    @property
    def instance(self):
        """
        Instance of the log entry - To subclass
        """
        raise NotImplementedError

    def publish(self):
        """
        Publish the log entry to the messaging system, broadcasting it to subscribers
        """
        logger.log(self.level_integer, self.text)

        if self.level in PUBLISHED_LOG_LEVEL_SET:
            publish_data('log', {
                'type': 'instance_log',
                'instance_pk': self.instance.pk,
                'log_entry': str(self),
            })


class InstanceLogEntry(LogEntry):
    """
    Single log entry for instances
    """
    instance = models.ForeignKey(OpenEdXInstance, related_name='logentry_set')


class ServerLogEntry(LogEntry):
    """
    Single log entry for servers
    """
    server = models.ForeignKey(OpenStackServer, related_name='logentry_set')

    @property
    def instance(self):
        """
        Instance of the server
        """
        return self.server.instance
