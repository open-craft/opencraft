"""
Instance app models - Logging
"""
#pylint: disable=no-init


# Imports #####################################################################

from swampdragon.pubsub_providers.data_publisher import publish_data

from django.db import models
from django.db.models import query
from django_extensions.db.models import TimeStampedModel


# Constants ###################################################################

LOG_LEVEL_CHOICES = (
    ('debug', 'Debug'),
    ('info', 'Info'),
    ('warn', 'Warning'),
    ('error', 'Error'),
    ('exception', 'Exception'),
)

LOG_LEVEL_SENT_TO_CLIENT = ('info', 'warn', 'error')


# Logging #####################################################################

import logging
logger = logging.getLogger(__name__)


# Models ######################################################################

class LogEntryQuerySet(query.QuerySet):
    '''
    Additional methods for LogEntry querysets
    Also used as the standard manager for the model (`LogEntry.objects`)
    '''
    def create(self, publish=True, *args, **kwargs):
        log_entry = super().create(*args, **kwargs)
        if publish:
            log_entry.publish()


class LogEntry(TimeStampedModel):
    '''
    Single log entry
    '''
    text = models.TextField()
    level = models.CharField(max_length=5, db_index=True, default='info', choices=LOG_LEVEL_CHOICES)

    objects = LogEntryQuerySet().as_manager()

    class Meta:
        abstract = True

    @property
    def level_integer(self):
        return logging.__dict__[self.level.upper()]

    def publish(self):
        logger.log(self.level_integer, self.text)

        if self.level in LOG_LEVEL_SENT_TO_CLIENT:
            publish_data('log', {
                'type': 'instance_log',
                'instance_pk': self.instance.pk,
                'log_entry': self.text,
            })


class InstanceLogEntry(LogEntry):
    '''
    Single log entry for instances
    '''
    instance = models.ForeignKey('OpenEdXInstance', related_name='logentry_set')


class ServerLogEntry(LogEntry):
    '''
    Single log entry for servers
    '''
    server = models.ForeignKey('OpenStackServer', related_name='logentry_set')

    @property
    def instance(self):
        return self.server.instance


class LoggerMixin(models.Model):
    '''
    Logging facilities - Logs stored on the model & shared with the client via websocket
    '''

    class Meta:
        abstract = True

    def log(self, level, text, **kwargs):
        self.logentry_set.create(level=level, text=text.rstrip(), **kwargs)
