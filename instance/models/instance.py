# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
Instance app models - Open EdX Instance and AppServer models
"""

# Imports #####################################################################

import logging

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.functional import cached_property
from django_extensions.db.models import TimeStampedModel
from swampdragon.pubsub_providers.data_publisher import publish_data

from instance.models.log_entry import LogEntry
from instance.logging import ModelLoggerAdapter
from .utils import ValidateModelMixin


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Models ######################################################################


class InstanceReference(TimeStampedModel):
    """
    InstanceReference: Holds common fields and provides a list of all Instances

    Has name, created, and modified fields for each Instance.

    Instance is an abstract class, so having this common InstanceReference class gives us a
    fully generic way to iterate through all instances and allow instances to be implemented
    using a variety of different python classes and database tables.
    """
    name = models.CharField(max_length=250, blank=False, default='Instance')
    instance_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    instance_id = models.PositiveIntegerField()
    instance = GenericForeignKey('instance_type', 'instance_id')

    class Meta:
        ordering = ['-created']
        unique_together = ('instance_type', 'instance_id')
        permissions = (
            ("manage_all", "Can manage all instances."),
        )

    def __str__(self):
        return '{} #{}'.format(self.instance_type.name, self.instance_id)

    def delete(self, *args, **kwargs):
        """
        Delete this InstanceReference and the associated Instance.
        """
        if not kwargs.pop('instance_already_deleted', False):
            self.instance.delete(ref_already_deleted=True)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Save this InstanceReference

        This also gets called whenever the Instance subclass has changed.
        """
        super().save(*args, **kwargs)
        # Notify anyone monitoring for changes via swampdragon/websockets:
        publish_data('notification', {
            'type': 'instance_update',
            'instance_id': self.pk,
        })

    @classmethod
    def can_manage(cls, user):
        """
        Returns true if the user has "instance.manage_all" permission
        """
        permission = '{}.{}'.format(cls._meta.app_label, "manage_all")
        return user.has_perm(permission)


class Instance(ValidateModelMixin, models.Model):
    """
    Instance: A web application or suite of web applications.

    An 'Instance' consists of an 'active' AppServer which is available at the instance's URL and
    handles all requests from users; the instance may also own some 'terminated' AppServers that
    are no longer used, and 'upcoming' AppServers that are used for testing before being
    designated as 'active'.

    In the future, we may add a scalable instance type, which owns a pool of active AppServers
    that all handle requests; currently at most one AppServer is active at any time.
    """
    # Reverse accessor to get the 'InstanceReference' set. This is a 1:1 relation, so use the
    # 'ref' property instead of accessing this directly. The only time to use this directly is
    # in a query, e.g. to do .select_related('ref_set')
    ref_set = GenericRelation(InstanceReference, content_type_field='instance_type', object_id_field='instance_id')

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ModelLoggerAdapter(logger, {'obj': self})

    def __str__(self):
        return str(self.ref)

    @cached_property
    def ref(self):
        """ Get the InstanceReference for this Instance """
        try:
            return self.ref_set.get()  # pylint: disable=no-member
        except ObjectDoesNotExist:
            return InstanceReference(instance=self)

    @property
    def name(self):
        """ Get this instance's name, which is stored in the InstanceReference """
        return self.ref.name

    @name.setter
    def name(self, new_name):
        """ Change the 'name' """
        self.ref.name = new_name

    @property
    def created(self):
        """ Get this instance's created date, which is stored in the InstanceReference """
        return self.ref.created

    @property
    def modified(self):
        """ Get this instance's modified date, which is stored in the InstanceReference """
        return self.ref.modified

    def save(self, *args, **kwargs):
        """ Save this Instance """
        super().save(*args, **kwargs)
        # Ensure an InstanceReference exists, and update its 'modified' field:
        if self.ref.instance_id is None:
            self.ref.instance_id = self.pk  # <- Fix needed when self.ref is accessed before the first self.save()
        self.ref.save()

    def refresh_from_db(self, using=None, fields=None, **kwargs):
        """
        Reload from DB, or load related field.

        We override this to ensure InstanceReference is reloaded too.
        Otherwise, the name/created/modified properties could be out of date, even after
        Instance.refresh_from_db() is called.
        """
        if fields is None:
            self.ref.refresh_from_db()
        super().refresh_from_db(using=using, fields=fields, **kwargs)

    @property
    def event_context(self):
        """
        Context dictionary to include in events
        """
        return {'instance_id': self.ref.pk, 'instance_type': self.__class__.__name__}

    def get_log_message_annotation(self):
        """
        Get annotation for log message for this instance.
        """
        return 'instance={} ({!s:.15})'.format(self.ref.pk, self.ref.name)

    @property
    def log_entries(self):
        """
        Return the list of log entry instances for this Instance.

        Does NOT include log entries of associated AppServers or Servers (VMs)
        """
        limit = settings.LOG_LIMIT

        instance_type = ContentType.objects.get_for_model(self)
        entries = LogEntry.objects.filter(content_type=instance_type, object_id=self.pk)
        # TODO: Filter out log entries for which the user doesn't have view rights
        return reversed(list(entries[:limit]))

    def delete(self, *args, **kwargs):
        """
        Delete this Instance.

        This will delete the InstanceReference at the same time.
        """
        if not kwargs.pop('ref_already_deleted', False):
            self.ref.delete(instance_already_deleted=True)
        super().delete(*args, **kwargs)
