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
Instance app - Report IP address of active appservers
"""

# Imports #####################################################################

import time
import logging

from instance.models.server import Status as ServerStatus
from instance.management.commands.instance_filter import Command as InstanceFilterCommand

LOG = logging.getLogger(__name__)

# Classes #####################################################################


class Command(InstanceFilterCommand):
    """
    instance_redeploy management command class
    """
    help = (
        'Redeploys a given set of instances by updating their configuration, spawning new new appservers, and'
        ' activating them when successful.'
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.options = {}
        self.retried = {}

    def handle(self, *args, **options):
        """
        For each filtered instance, locate any running appservers and print their IP addresses.
        """
        self.options = options
        for instance in self.get_instances().all():
            public_domain = instance.external_lms_domain or instance.internal_lms_domain
            print("[{public_domain}]".format(public_domain=public_domain))
            for appserver in instance.appserver_set.filter(server___status=ServerStatus.Ready.state_id):
                if appserver.server.public_ip:
                    print("{public_ip} # {appserver}".format(public_ip=appserver.server.public_ip,
                                                             appserver=appserver))

            print("")
