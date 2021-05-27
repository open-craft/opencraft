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
Instance app models - LogEntry
"""

# Imports #####################################################################

import logging

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django_extensions.db.models import TimeStampedModel

from .utils import ValidateModelMixin

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
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    level = models.CharField(max_length=9, db_index=True, default='INFO', choices=LOG_LEVEL_CHOICES)

    class Meta:
        ordering = ('-created', )
        index_together = [
            ['content_type', 'object_id'],
        ]
        permissions = (
            ("read_log_entry", "Can read LogEntry"),
        )
        verbose_name_plural = "Log Entries"

    def __str__(self):
        return '{0.created:%Y-%m-%d %H:%M:%S} | {0.level:>8s} | {0.text}'.format(self)

    def clean_fields(self, **kwargs):  # pylint: disable=arguments-differ
        """
        Clean fields, including the 'object_id' field
        """
        super().clean_fields(**kwargs)
        # This check is here rather than in clean() because it must come after the built-in
        # validation of the content_type field, and we should only check object_id if
        # content_type has passed validation.
        if self.content_type_id or self.object_id:
            # If either of these fields are set, both should be:
            if not self.content_type_id or not self.object_id:
                raise ValidationError('LogEntry content_type and object_id must both be set or both be None.')
            # Ensure that the object_id (primary key) is valid:
            if not self.content_type.get_all_objects_for_this_type(pk=self.object_id).exists():
                raise ValidationError({'object_id': 'Object attached to LogEntry has bad content_type or primary key'})

    @staticmethod
    def on_post_delete(sender, instance, **kwargs):
        """
        Whenever an object is deleted, check if there are corresponding log entries to delete.
        """
        if isinstance(instance, LogEntry) or instance._meta.app_label == 'migrations':
            return  # Avoid pointless database queries when deleting log entries themselves or saving migration history
        if not isinstance(instance.pk, int):
            return  # Current LogEntry schema requires integer objects IDs, so we know this object isn't in the table
        content_type = ContentType.objects.get_for_model(instance)
        num_deleted, dummy = LogEntry.objects.filter(content_type=content_type, object_id=instance.pk).delete()
        if num_deleted > 0:
            logger.info(
                'Deleted %d log entries for deleted %s instance with ID %d',
                num_deleted, content_type.name, instance.pk
            )


post_delete.connect(LogEntry.on_post_delete)
