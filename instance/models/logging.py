"""
Instance app models - Logging
"""
#pylint: disable=no-init


# Imports #####################################################################

from swampdragon.pubsub_providers.data_publisher import publish_data

from django.db import models
from django.db.models import Q, query
from django_extensions.db.models import TimeStampedModel


# Constants ###################################################################

LOG_LEVEL_CHOICES = (
    ('debug', 'Debug'),
    ('info', 'Info'),
    ('warn', 'Warning'),
    ('error', 'Error'),
    ('exception', 'Exception'),
)

PUBLISHED_LOG_LEVEL_SET = ('info', 'warn', 'error')


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

    def __str__(self):
        return '{0.created:%Y-%m-%d %H:%M:%S} [{0.level}] {0.text}'.format(self)

    @property
    def level_integer(self):
        return logging.__dict__[self.level.upper()]

    def publish(self):
        logger.log(self.level_integer, self.text)

        if self.level in PUBLISHED_LOG_LEVEL_SET:
            publish_data('log', {
                'type': 'instance_log',
                'instance_pk': self.instance.pk,
                'log_entry': str(self),
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


class LoggerInstanceMixin(LoggerMixin):
    '''
    Logging facilities - Instances
    '''
    class Meta:
        abstract = True

    @property
    def log_text(self):
        '''
        Combines the instance and server log outputs in chronological order
        Currently only supports one non-terminated server at a time
        Returned as a text string
        '''
        current_server = self.server_set.get(~Q(status='terminated'))
        server_logentry_set = current_server.logentry_set.filter(level__in=PUBLISHED_LOG_LEVEL_SET)\
                                                         .order_by('pk')\
                                                         .iterator()
        instance_logentry_set = self.logentry_set.filter(level__in=PUBLISHED_LOG_LEVEL_SET)\
                                                         .order_by('pk')\
                                                         .iterator()

        def next_instance_logentry():
            try:
                return next(instance_logentry_set)
            except StopIteration:
                return None

        def next_server_logentry():
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
