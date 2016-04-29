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

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.functional import cached_property
from django_extensions.db.models import TimeStampedModel

from instance.logger_adapter import InstanceLoggerAdapter
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

    def __str__(self):
        return '{} #{}'.format(self.instance_type.name, self.instance_id)


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

        self.logger = InstanceLoggerAdapter(logger, {'obj': self})

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
        self.ref.save()  # pylint: disable=no-member

    @property
    def event_context(self):
        """
        Context dictionary to include in events
        """
        return {'instance_id': self.ref.pk}
