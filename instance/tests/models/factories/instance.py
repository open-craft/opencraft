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
SingleVMOpenEdXInstance model - Factories
"""

# Imports #####################################################################

import factory
from factory.django import DjangoModelFactory

from instance.models.instance import SingleVMOpenEdXInstance


# Classes #####################################################################

class SingleVMOpenEdXInstanceFactory(DjangoModelFactory):
    """
    Factory for SingleVMOpenEdXInstance
    """
    class Meta: #pylint: disable=missing-docstring
        model = SingleVMOpenEdXInstance

    sub_domain = factory.Sequence('instance{}.test'.format)
    name = factory.Sequence('Test Instance {}'.format)
    commit_id = factory.Sequence('{:>040}'.format)
    github_organization_name = factory.Sequence('test-org{}'.format)
    github_repository_name = factory.Sequence('test-repo{}'.format)

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        """ Force FactoryBoy to set the field '_status' even though it starts with an underscore """
        if 'status' in kwargs:
            kwargs['_status'] = kwargs.pop('status').state_id
        if hasattr(cls, '_status') and '_status' not in kwargs:
            kwargs['_status'] = cls._status  # pylint: disable=no-member
        return kwargs


class WaitingSingleVMOpenEdXInstanceFactory(SingleVMOpenEdXInstanceFactory):
    """
    Factory for an instance with a 'waiting' state
    """
    _status = SingleVMOpenEdXInstance.Status.WaitingForServer.state_id


class ConfiguringSingleVMOpenEdXInstanceFactory(SingleVMOpenEdXInstanceFactory):
    """
    Factory for an instance with a 'configuring' state
    """
    _status = SingleVMOpenEdXInstance.Status.ConfiguringServer.state_id


class RunningSingleVMOpenEdXInstanceFactory(SingleVMOpenEdXInstanceFactory):
    """
    Factory for an instance with a 'running' state
    """
    _status = SingleVMOpenEdXInstance.Status.Running.state_id


class ConfigFailedSingleVMOpenEdXInstanceFactory(SingleVMOpenEdXInstanceFactory):
    """
    Factory for an instance with a 'failed' state
    """
    _status = SingleVMOpenEdXInstance.Status.ConfigurationFailed.state_id


class ErrorSingleVMOpenEdXInstanceFactory(SingleVMOpenEdXInstanceFactory):
    """
    Factory for an instance with an 'error' state
    """
    _status = SingleVMOpenEdXInstance.Status.Error.state_id


class TerminatedSingleVMOpenEdXInstanceFactory(SingleVMOpenEdXInstanceFactory):
    """
    Factory for an instance with a 'terminated' state
    """
    _status = SingleVMOpenEdXInstance.Status.Terminated.state_id
