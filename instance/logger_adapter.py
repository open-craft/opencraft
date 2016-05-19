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
Instance app models - Logger Adapters
"""

# Imports #####################################################################

import logging

# Helper methods ##############################################################


def format_instance(instance):
    """ Given any concrete subclass of Instance, get a short ID string to put into the log """
    if instance:
        return 'instance={} ({!s:.15})'.format(instance.ref.pk, instance.ref.name)
    return 'Unknown Instance'


def format_appserver(app_server):
    """ Given an AppServer subclass, get a short ID string to put into the log """
    if app_server:
        return 'app_server={} ({!s:.15})'.format(app_server.pk, app_server.name)
    return 'Unknown AppServer'


def format_server(server):
    """ Given a Server subclass, get a short ID string to put into the log """
    if server:
        return 'server={!s:.20}'.format(server.name)
    return 'Unknown Server'

# Adapters ####################################################################


class AppServerLoggerAdapter(logging.LoggerAdapter):
    """
    Custom LoggerAdapter for Instance objects
    Include the instance name in the output
    """
    def process(self, msg, kwargs):
        msg, kwargs = super().process(msg, kwargs)

        app_server = self.extra['obj']
        if app_server.instance:
            msg = '{},{} | {}'.format(format_instance(app_server.instance), format_appserver(app_server), msg)
        return msg, kwargs


class ServerLoggerAdapter(logging.LoggerAdapter):
    """
    Custom LoggerAdapter for Server objects
    Include the instance & server names in the output
    """
    def process(self, msg, kwargs):
        msg, kwargs = super().process(msg, kwargs)

        server = self.extra['obj']
        msg = '{} | {}'.format(format_server(server), msg)
        return msg, kwargs


class InstanceLoggerAdapter(logging.LoggerAdapter):
    """
    Custom LoggerAdapter for Instance objects
    Include the InstanceReference ID in the output
    """
    def process(self, msg, kwargs):
        msg, kwargs = super().process(msg, kwargs)

        instance = self.extra['obj']
        msg = '{} | {}'.format(format_instance(instance), msg)
        return msg, kwargs
