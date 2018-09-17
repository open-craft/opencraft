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
Module with tools that performs backups.
"""

# Imports #####################################################################

import datetime
import logging

from django.conf import settings
from django.core.mail import mail_admins
from huey.api import crontab
from huey.contrib.djhuey import db_task, db_periodic_task
from swiftclient.service import SwiftError

from backup_swift.tarsnap import make_tarsnap_backup
from backup_swift.utils import ping_heartbeat_url, filter_logger, filter_swift

from instance import openstack_utils

# Logging #####################################################################

logger = logging.getLogger(__name__)

# Functions #####################################################################


def do_backup_swift():
    """
    Perform full swift backup sequence.
    """

    with filter_logger('swiftclient.service', filter_swift), filter_logger('swiftclient', filter_swift):

        logger.info("Starting backup of swift containers")
        error_report = ""
        download_results = []
        try:
            download_results = openstack_utils.download_swift_account(settings.BACKUP_SWIFT_TARGET)
        except SwiftError:
            error_report += "Miscellaneous error while downloading swift containers\n"
            logger.exception("Misc error while downloading swift containers")

        if download_results:
            error_report += "Following containers failed to download:\n"
            for container in download_results:
                error_report += "#. {name}; Failed files: {count}.\n".format(
                    name=container.name, count=container.number_of_failures
                )
                error_report += "Extra information: \n{extra_info}".format(
                    extra_info=container.extra_information
                )

        # In case of downloading errors run tarsnap nevertheless, so we at least backup something.

        tarsnap_successful = make_tarsnap_backup(
            keyfile=settings.BACKUP_SWIFT_TARSNAP_KEY_LOCATION,
            cachedir=settings.BACKUP_SWIFT_TARSNAP_CACHE_LOCATION,
            directory=settings.BACKUP_SWIFT_TARGET,
            archive_name="{}-{}".format(
                settings.BACKUP_SWIFT_TARSNAP_KEY_ARCHIVE_NAME, datetime.datetime.now().isoformat()
            )
        )

        if not tarsnap_successful:
            error_report += "Error while running tarsnap\n"

        if error_report:
            error_report += "Please check the server logs, they might contain more details."
            mail_admins("Error when backing up swift containers", error_report)
            logger.error("Error when backing up swift containers\b %s", error_report)
        else:
            logger.info("Swift backup finished successfully")
            if settings.BACKUP_SWIFT_SNITCH:
                ping_heartbeat_url(settings.BACKUP_SWIFT_SNITCH)


@db_task()
def backup_swift_task():
    """
    Task that performs backup of swift containers.
    """
    do_backup_swift()


if settings.BACKUP_SWIFT_ENABLED:

    @db_periodic_task(crontab(minute="10", hour="1"))
    def backup_swift_periodic():
        """
        Periodically schedules backup_swift_task.

        This is long running task, more like spawn_appserver than watch_pr,
        since we a single queue for periodic tasks it makes sense for this to finish
        early and then execute in another worker.
        """
        backup_swift_task()
