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
Test utils
"""

# Imports #####################################################################

from contextlib import ExitStack
from unittest.mock import Mock, patch
import requests
import responses

from instance import gandi
from instance.tests.fake_gandi_client import FakeGandiClient
from instance.tests.models.factories.server import OSServerMockManager


# Functions ###################################################################

def patch_gandi(func=None):
    """
    Decorator to temporarily replace the Gandi API by the fake implementation.
    """
    patcher = patch('instance.gandi.api', gandi.GandiAPI(client=FakeGandiClient()))
    if func:
        return patcher(func)
    return patcher


def patch_url(url, method=responses.GET, status=requests.codes.ok):
    """
    Decorator which mocks responses from the given url.

    Arguments:

    * `url`: http url to mock
    * `method`: http method used in request (default responses.GET)
    * `status`: http status returned by response (default requests.codes.ok)

    Usage:

    E.g., to mock POST requests to the OpenStack authentication URL:

        import responses
        from django.conf import settings
        from instance.tests.utils import patch_url

        @patch_url(settings.OPENSTACK_AUTH_URL, method=responses.POST)
        def test_that_calls_nova(...):
            ...
    """
    def function_wrapper(func):
        def responses_wrapper(*args, **kwargs):
            responses.add(
                method=method,
                url=url,
                status=status,
            )
        return responses_wrapper(func)
    return function_wrapper


def patch_services(func):
    """
    Mock most external services so that things 'seem to work' when provisioning a server.

    Returns a mock containing all the mocked services, so each test can customize the process.
    """
    new_servers = [Mock(id='server1'), Mock(id='server2'), Mock(id='server3'), Mock(id='server4')]

    def wrapper(self, *args, **kwargs):
        """ Wrap the test with appropriate mocks """
        os_server_manager = OSServerMockManager()
        os_server_manager.set_os_server_attributes('server1', _loaded=True, status='ACTIVE')

        with ExitStack() as stack:
            def stack_patch(*args, **kwargs):
                """ Add another patch to the context and return its mock """
                return stack.enter_context(patch(*args, **kwargs))

            mock_sleep = stack_patch('instance.models.server.time.sleep')
            mock_get_nova_client = stack_patch('instance.models.server.openstack_utils.get_nova_client')
            mock_get_nova_client.return_value.servers.get = os_server_manager.get_os_server

            def check_sleep_count(_delay):
                """ Check that time.sleep() is not used in some sort of infinite loop """
                self.assertLess(mock_sleep.call_count, 1000, "time.sleep() called too many times.")
            mock_sleep.side_effect = check_sleep_count

            mocks = Mock(
                os_server_manager=os_server_manager,
                mock_get_nova_client=mock_get_nova_client,
                mock_is_port_open=stack_patch('instance.models.server.is_port_open', return_value=True),
                mock_create_server=stack_patch(
                    'instance.models.server.openstack_utils.create_server', side_effect=new_servers,
                ),
                mock_sleep=mock_sleep,
                mock_run_ansible_playbooks=stack_patch(
                    'instance.models.mixins.ansible.AnsibleAppServerMixin.run_ansible_playbooks',
                    return_value=([], 0),
                ),
                mock_provision_failed_email=stack_patch(
                    'instance.models.mixins.utilities.EmailMixin.provision_failed_email',
                ),
                mock_check_security_groups=stack_patch(
                    'instance.models.openedx_appserver.OpenEdXAppServer.check_security_groups',
                ),
                mock_provision_mysql=stack_patch(
                    'instance.models.mixins.openedx_database.MySQLInstanceMixin.provision_mysql',
                ),
                mock_provision_mongo=stack_patch(
                    'instance.models.mixins.openedx_database.MongoDBInstanceMixin.provision_mongo',
                ),
                mock_provision_swift=stack_patch(
                    'instance.models.mixins.openedx_storage.SwiftContainerInstanceMixin.provision_swift'
                ),
                mock_load_balancer_run_playbook=stack_patch(
                    'instance.models.load_balancer.LoadBalancingServer.run_playbook'
                ),
                mock_enable_monitoring=stack_patch(
                    'instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.enable_monitoring'
                ),
                mock_disable_monitoring=stack_patch(
                    'instance.models.mixins.openedx_monitoring.OpenEdXMonitoringMixin.disable_monitoring'
                ),
            )
            stack.enter_context(patch_gandi())
            return func(self, mocks, *args, **kwargs)
    return wrapper
