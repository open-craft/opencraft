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
from django.db.models import Q, query
from django_extensions.db.models import TimeStampedModel

import instance #pylint: disable=unused-import


# Constants ###################################################################

LOG_LEVEL_CHOICES = (
    ('debug', 'Debug'),
    ('info', 'Info'),
    ('warn', 'Warning'),
    ('error', 'Error'),
    ('exception', 'Exception'),
)

PUBLISHED_LOG_LEVEL_SET = ('info', 'warn', 'error')

__all__ = ['InstanceLogEntry', 'ServerLogEntry']


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


class LogEntry(TimeStampedModel):
    """
    Single log entry
    """
    text = models.TextField()
    level = models.CharField(max_length=5, db_index=True, default='info', choices=LOG_LEVEL_CHOICES)

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
        return logging.__dict__[self.level.upper()]


class InstanceLogEntry(LogEntry):
    """
    Single log entry for instances
    """
    instance = models.ForeignKey(instance.models.instance.OpenEdXInstance, related_name='logentry_set')

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


class ServerLogEntry(LogEntry):
    """
    Single log entry for servers
    """
    server = models.ForeignKey(instance.models.server.OpenStackServer, related_name='logentry_set')

    @property
    def instance(self):
        """
        Instance of the server
        """
        return self.server.instance


class LoggerMixin(models.Model):
    """
    Logging facilities - Logs stored on the model & shared with the client via websocket
    """
    class Meta:
        abstract = True

    def log(self, level, text, **kwargs):
        """
        Log an entry text at a specified level
        """
        self.logentry_set.create(level=level, text=text.rstrip(), **kwargs)


class LoggerInstanceMixin(LoggerMixin):
    """
    Logging facilities - Instances
    """
    class Meta:
        abstract = True

    @property
    def log_text(self):
        """
        Combines the instance and server log outputs in chronological order
        Currently only supports one non-terminated server at a time
        Returned as a text string
        """
        current_server = self.server_set.get(~Q(status='terminated'))
        server_logentry_set = current_server.logentry_set.filter(level__in=PUBLISHED_LOG_LEVEL_SET)\
                                                         .order_by('pk')\
                                                         .iterator()
        instance_logentry_set = self.logentry_set.filter(level__in=PUBLISHED_LOG_LEVEL_SET)\
                                                 .order_by('pk')\
                                                 .iterator()

        def next_instance_logentry():
            """ Get the next log entry from the instance logs iterator """
            try:
                return next(instance_logentry_set)
            except StopIteration:
                return None

        def next_server_logentry():
            """ Get the next log entry from the server logs iterator """
            try:
                return next(server_logentry_set)
            except StopIteration:
                return None

        log_text = ''
        instance_logentry = next_instance_logentry()
        server_logentry = next_server_logentry()

        while True:
            if instance_logentry is None and server_logentry is None:
                break
            elif instance_logentry is None or \
                    (server_logentry is not None and server_logentry.created < instance_logentry.created):
                log_text += '{}\n'.format(server_logentry)
                server_logentry = next_server_logentry()
            else:
                log_text += '{}\n'.format(instance_logentry)
                instance_logentry = next_instance_logentry()

        return log_text
