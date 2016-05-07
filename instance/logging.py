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
Instance app - Logging utils
"""

# Imports #####################################################################

from functools import wraps
import logging
import traceback

from django.apps import apps
from django.db import models
from swampdragon.pubsub_providers.data_publisher import publish_data

from instance.serializers.logentry import LogEntrySerializer


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Functions ###################################################################

def log_exception(method):
    """
    Decorator to log uncaught exceptions on methods
    Uses the object logging facilities, ie `self.logger` must be defined
    """
    @wraps(method)
    def wrapper(self, *args, **kwds): #pylint: disable=missing-docstring
        try:
            return method(self, *args, **kwds)
        except:
            self.logger.critical(traceback.format_exc()) # TODO: Restrict traceback view to administrators
            raise
    return wrapper


# Classes #####################################################################

class DBHandler(logging.Handler):
    """
    Records log messages in database models
    """
    def emit(self, record):
        """
        Handles an emitted log entry and stores it in the database, optionally linking it to the
        model object `obj`
        """
        obj = record.__dict__.get('obj', None)

        if obj is None or not isinstance(obj, models.Model) or obj.pk is None:
            content_type, object_id = None, None
        else:
            content_type = apps.get_model('contenttypes', 'ContentType').objects.get_for_model(obj)
            object_id = obj.pk

        log_entry = apps.get_model('instance', 'LogEntry').objects.create(
            level=record.levelname, text=self.format(record), content_type=content_type, object_id=object_id
        )

        log_event = {
            'type': 'instance_log',
            'log_entry': LogEntrySerializer(log_entry).data
        }
        if hasattr(obj, 'event_context'):
            log_event.update(obj.event_context)

        # Send notice of entries related to any resource. Skip generic log entries that occur
        # in debug mode, like "GET /static/img/favicon/favicon-96x96.png":
        if content_type:
            # TODO: Filter out log entries for which the user doesn't have view rights
            publish_data('log', log_event)
