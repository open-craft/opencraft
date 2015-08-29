#!/usr/bin/env python
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
OpenStack management command
"""

# Imports #####################################################################

import sys

from django.core.management.base import BaseCommand, CommandError

from instance.openstack import OpenStackClient

# Functions ###################################################################

class Command(BaseCommand):
    help = 'Run the openstack command with the specified cluster environment'
def run(cluster_name):
    cluster_name = sys.argv[1]
    command = ' '.join(sys.argv[2:])
    os_client = OpenStackClient(cluster_name=cluster_name)
    return os_client.run(command)


# Main ########################################################################

if __name__ == '__main__':
    print(run())
