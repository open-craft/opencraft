# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
Management command to clean old appserver's logs.
"""

# Imports #####################################################################

import datetime
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.test import override_settings

from instance.models.log_entry import LogEntry
from instance.models.openedx_appserver import OpenEdXAppServer

LOG = logging.getLogger(__name__)

# Classes #####################################################################


class Command(BaseCommand):
    """
    Management command to clean old appserver's logs.
    """
    help = (
        "Clean old appserver's deployment logs to save up space in the database."
        "Logs will be replaced by a single line indicating they were deleted."
        "Only OpenEdxAppServer logs will be processed"
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.options = {}

    def add_arguments(self, parser):
        """
        Add named arguments.
        """
        parser.add_argument(
            '--months-old',
            type=int,
            default=6,
            help='Number of months after which an appserver is considered old. Servers older than this will have '
                 'their logs deleted'
        )

    def handle(self, *args, **options):
        """
        Clean old logs.
        """
        self.options = options
        now = datetime.datetime.now()
        cut_date = now - datetime.timedelta(days=30.4 * self.options['months_old'])
        appserver_type = ContentType.objects.get_for_model(OpenEdXAppServer)

        old_appservers = OpenEdXAppServer.objects.filter(created__lt=cut_date)

        for appserver in old_appservers:
            LOG.info(
                "Processing appserver %i (for instance %i, %s)",
                appserver.id,
                appserver.instance.id,
                appserver.instance.internal_lms_domain
            )
            # We use QuerySet instead of appserver.log_entries because the latter is caped to settings.LOG_LIMIT
            logs = LogEntry.objects.filter(content_type=appserver_type, object_id=appserver.pk)
            if logs.count() == 1:
                LOG.info("Appserver %i's logs are already small or reduced", appserver.id)
            else:
                LOG.info("Cleaning logs for appserver %i", appserver.id)
                logs.delete()
                appserver.logger.info("Logs were deleted at {}".format(now))
