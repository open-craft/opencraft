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
Instance app models - Logger Adapters
"""

# Imports #####################################################################

import logging


# Adapters ####################################################################

class InstanceLoggerAdapter(logging.LoggerAdapter):
    """
    Custom LoggerAdapter for Instance objects
    Include the instance name in the output
    """
    def process(self, msg, kwargs):
        msg, kwargs = super().process(msg, kwargs)

        if self.extra.get('obj', None):
            return 'instance={} | {}'.format(self.extra['obj'].sub_domain, msg), kwargs
        else:
            return msg, kwargs


class ServerLoggerAdapter(logging.LoggerAdapter):
    """
    Custom LoggerAdapter for Server objects
    Include the instance & server names in the output
    """
    def process(self, msg, kwargs):
        msg, kwargs = super().process(msg, kwargs)

        if self.extra.get('obj', None):
            server = self.extra['obj']
            return 'instance={!s:.15},server={!s:.8} | {}'.format(server.instance.sub_domain, server, msg), kwargs
        else:
            return msg, kwargs
