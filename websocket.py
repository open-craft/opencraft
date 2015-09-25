#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
Websocket server, based on Tornado & SwampDragon
"""

# Imports #####################################################################

import os
import sys

from swampdragon.swampdragon_server import run_server


# Django ######################################################################

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opencraft.settings")
from django.conf import settings


# Main ########################################################################

host_port = sys.argv[1] if len(sys.argv) > 1 else settings.DRAGON_SERVER_ADDRESS_PORT
run_server(host_port=host_port)
