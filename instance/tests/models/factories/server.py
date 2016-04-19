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
from functools import wraps
from mock import MagicMock, Mock, patch

from instance.models.server import OpenStackServer
from instance.tests.base import add_fixture_to_object
from instance.tests.models.factories.instance import SingleVMOpenEdXInstanceFactory


# Functions ###################################################################

def patch_os_server(func):
    """
    To patch `Server.os_server` (OpenStack API Server answer) in unit tests

    Adds a `os_server_manager` to the decorated function (see `OSServerMockManager`)
    which can be used to set attributes or fixtures on the mock object returned by
    `Server.nova.servers.get()` for a given `openstack_id`
    """
    os_server_manager = OSServerMockManager()

    def server_get(openstack_id): #pylint: disable=missing-docstring
        return os_server_manager.get_os_server(openstack_id)

    @wraps(func)
    def wrapper(*args, **kwargs): #pylint: disable=missing-docstring
        with patch('instance.models.server.openstack.get_nova_client') as mock_get_nova_client:
            mock_get_nova_client.return_value.servers.get.side_effect = server_get
            args += (os_server_manager,)
            func(*args, **kwargs)
    return wrapper


# Classes #####################################################################

class OSServerMockManager:
    """
    Manager of Mock objects used by `patch_os_server`

    Contains a dictionary of mock `os_server`, identified by `openstack_id`
    Allows to set custom attributes on individual `os_server` mocks (or entire fixtures)

    Defaults to standard MagicMock if no attribute of fixture has been loaded for a given `openstack_id`
    """
    def __init__(self):
        self._os_server_dict = {}

    def get_os_server(self, openstack_id):
        """
        Returns the mock `os_server` for this `openstack_id`
        """
        if openstack_id not in self._os_server_dict.keys():
            self._os_server_dict[openstack_id] = MagicMock(addresses={"Ext-Net": [{"addr": "1.1.1.1", }]})
        return self._os_server_dict[openstack_id]

    def set_os_server_attributes(self, openstack_id, **attributes):
        """
        Set the attributes on the mock `os_server` returned for this `openstack_id`
        """
        self.get_os_server(openstack_id).__dict__.update(attributes)

    def add_fixture(self, openstack_id, fixture_filename):
        """
        Add the contents of a fixture to the mock `os_server` attributes for this `openstack_id`
        """
        add_fixture_to_object(self.get_os_server(openstack_id), fixture_filename)


class OpenStackServerFactory(DjangoModelFactory):
    """
    Factory for OpenStackServer
    """
    class Meta: #pylint: disable=missing-docstring
        model = OpenStackServer

    instance = factory.SubFactory(SingleVMOpenEdXInstanceFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        os_server_fixture = kwargs.pop('os_server_fixture', None)
        server = super()._create(model_class, *args, **kwargs)

        # This isn't a model field, so it needs to be set separately, not passed to the model `__init__`
        server.nova = Mock()

        # Allow to set OpenStack API data for the current `self.os_server`, using fixtures
        if os_server_fixture is not None:
            add_fixture_to_object(server.nova.servers.get.return_value, os_server_fixture)

        return server

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        """ Force FactoryBoy to set the field '_status' even though it starts with an underscore """
        if 'status' in kwargs:
            kwargs['_status'] = kwargs.pop('status').state_id
        if 'progress' in kwargs:
            kwargs['_progress'] = kwargs.pop('progress').state_id
        if hasattr(cls, '_status') and '_status' not in kwargs:
            kwargs['_status'] = cls._status  # pylint: disable=no-member
        return kwargs


class StartedOpenStackServerFactory(OpenStackServerFactory):
    """
    Factory for a server with a 'started' state
    """
    _status = OpenStackServer.Status.Started.state_id
    openstack_id = factory.Sequence('started-server-id{}'.format)


class BootedOpenStackServerFactory(OpenStackServerFactory):
    """
    Factory for a server with a 'booted' state
    """
    _status = OpenStackServer.Status.Booted.state_id
    openstack_id = factory.Sequence('booted-server-id{}'.format)


class ProvisioningOpenStackServerFactory(OpenStackServerFactory):
    """
    Factory for a server with a 'provisioning' state
    """
    _status = OpenStackServer.Status.Provisioning.state_id
    openstack_id = factory.Sequence('provisioning-server-id{}'.format)
