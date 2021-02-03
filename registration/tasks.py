# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <contact@opencraft.com>
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
Worker for BetaTestApplication management
"""

# Imports #####################################################################

import logging

from huey.contrib.djhuey import db_task

from registration.models import BetaTestApplication, DNSConfigState
from registration.utils import (
    is_external_domain_dns_configured,
    send_dns_not_configured_email
)

# Logging #####################################################################

logger = logging.getLogger(__name__)


# Tasks #######################################################################


@db_task()
def verify_external_domain_configuration(application_id: int) -> None:
    """
    Verify that the external_domain of the application is configured
    properly and update the status.
    """
    application = BetaTestApplication.objects.get(pk=application_id)
    is_pending = application.external_domain and application.dns_configuration_state == DNSConfigState.pending.name
    if is_pending:
        if is_external_domain_dns_configured(application.external_domain):
            application.dns_configuration_state = DNSConfigState.verified
        else:
            application.dns_configuration_state = DNSConfigState.failed
            send_dns_not_configured_email(application)
        application.save()
