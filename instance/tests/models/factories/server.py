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
OpenStackServer model - Factories
"""

# Imports #####################################################################

import factory
from factory.django import DjangoModelFactory
from mock import Mock

from instance.models.server import OpenStackServer
from instance.tests.base import add_fixture_to_object
from instance.tests.models.factories.instance import OpenEdXInstanceFactory


# Classes #####################################################################

class OpenStackServerFactory(DjangoModelFactory):
    """
    Factory for OpenStackServer
    """
    class Meta: #pylint: disable=missing-docstring
        model = OpenStackServer

    instance = factory.SubFactory(OpenEdXInstanceFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        os_server_fixture = kwargs.pop('os_server_fixture', None)
        server = super()._create(model_class, *args, **kwargs)

        # This isn't a model fields, so it needs to be set separately, not passed to the model `__init__`
        server.nova = Mock()

        # Allow to set OpenStack API data for the current `self.os_server`, using fixtures
        if os_server_fixture is not None:
            add_fixture_to_object(server.nova.servers.get.return_value, os_server_fixture)

        return server


class StartedOpenStackServerFactory(OpenStackServerFactory):
    """
    Factory for a server with a 'started' status
    """
    status = 'started'
    openstack_id = factory.Sequence('started-server-id{}'.format)
