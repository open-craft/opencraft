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
Instance app model mixins - Periodic builds
"""

# Imports #####################################################################
import datetime

from django.contrib.postgres.fields import ArrayField
from django.db import models


class OpenEdXPeriodicBuildsMixin(models.Model):
    """
    Mixin to provide support for periodic builds.
    """

    class Meta:
        abstract = True

    periodic_builds_enabled = models.BooleanField(
        default=False,
        help_text="Enable automatically rebuilding and deploying new appservers at intervals",
    )
    periodic_builds_interval = models.DurationField(
        default=datetime.timedelta(hours=24),
        help_text=(
            "Time interval between periodic builds. Note that this will not be precise; "
            "This interval will be the minimum time between the start of one build to the start of the next build. "
            "If a previous appserver is still provisioning when this interval is past, "
            "it will wait until it is finished before spawning a new appserver. "
            "Expects data in the format \"DD HH:MM:SS.uuuuuu\" or as specified by "
            "ISO 8601 (e.g. P4DT1H15M20S which is equivalent to 4 1:15:20) or "
            "PostgreSQL’s day-time interval format (e.g. 3 days 04:05:06)."
        ),
    )
    periodic_builds_retries = models.PositiveIntegerField(
        default=0, help_text="Number of times to retry spawning a new appserver if it fails (for periodic builds)."
    )
    periodic_build_failure_notification_emails = ArrayField(  # pylint: disable=invalid-name
        models.EmailField(),
        default=list,
        blank=True,
        help_text="Optional: Email address where notification must be sent if the build failed"
    )
