# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
LoadBalancingServer model - tests
"""
import re
from unittest.mock import Mock, patch

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from instance.models.load_balancer import LoadBalancingServer, ReconfigurationFailed
from instance.tests.base import TestCase
from instance.tests.models.factories.load_balancer import LoadBalancingServerFactory


def mock_instances():
    """
    Patch out the get_instances() method.
    """
    def make_mock_instance(domains, ip_address, backend_name):
        """
        Create a mock instance meant for load balancer testing.
        """
        instance = Mock()
        map_entries = [(domain, backend_name) for domain in domains]
        conf_entries = [(backend_name, "    server test-server {}:80".format(ip_address))]
        instance.get_load_balancer_configuration.return_value = map_entries, conf_entries
        return instance

    return [
        make_mock_instance(
            # We include an upper-case domain name here to be able to test it gets properly
            # converted to lower-case when the configuration is sent to the load balancer.
            ["test1.lb.opencraft.hosting", "TEST2.lb.opencraft.hosting"],
            "1.2.3.4",
            "first-backend",
        ),
        make_mock_instance(
            ["test3.lb.opencraft.hosting"],
            "5.6.7.8",
            "second-backend",
        ),
    ]


class LoadBalancingServerTest(TestCase):
    """
    Test cases for the LoadBalancingServer model.
    """

    def setUp(self):
        self.load_balancer = LoadBalancingServerFactory()

    @patch('instance.models.load_balancer.LoadBalancingServer.get_instances', return_value=mock_instances())
    def test_get_configuration(self, mock_get_instances):
        """
        Test that the configuration gets rendered correctly.
        """
        backend_map, backend_conf = self.load_balancer.get_configuration()
        self.assertCountEqual(
            [line for line in backend_map.splitlines(False) if line],
            [
                "test1.lb.opencraft.hosting first-backend" + self.load_balancer.fragment_name_postfix,
                "test2.lb.opencraft.hosting first-backend" + self.load_balancer.fragment_name_postfix,
                "test3.lb.opencraft.hosting second-backend" + self.load_balancer.fragment_name_postfix,
            ],
        )
        backends = [match.group(1) for match in re.finditer(r"^backend (\S*)", backend_conf, re.MULTILINE)]
        self.assertCountEqual(backends, [
            "first-backend" + self.load_balancer.fragment_name_postfix,
            "second-backend" + self.load_balancer.fragment_name_postfix,
        ])

    @patch("instance.ansible.poll_streams")
    @patch("instance.ansible.run_playbook")
    @patch('instance.models.load_balancer.LoadBalancingServer.get_instances', return_value=mock_instances())
    def test_reconfigure(self, mock_get_instances, mock_run_playbook, mock_poll_streams):
        """
        Test that the reconfigure() method triggers a playbook run.
        """
        mock_run_playbook.return_value.__enter__.return_value.returncode = 0
        self.load_balancer.reconfigure()
        #self.assertEqual(mock_run_playbook.call_count, 1)
        self.assertEqual(self.load_balancer.configuration_version, 2)
        self.assertEqual(self.load_balancer.deployed_configuration_version, 2)
        self.load_balancer.delete()
        #self.assertEqual(mock_run_playbook.call_count, 2)

    @patch("instance.ansible.poll_streams")
    @patch("instance.ansible.run_playbook")
    @patch('instance.models.load_balancer.LoadBalancingServer.get_instances', return_value=mock_instances())
    def test_reconfigure_fails(self, mock_get_instances, mock_run_playbook, mock_poll_streams):
        """
        Test that the reconfigure() method gives us a dirty LB if the playbook fails.
        """
        with self.assertRaises(ReconfigurationFailed):
            mock_run_playbook.return_value.__enter__.return_value.returncode = 1
            self.load_balancer.reconfigure()
            self.assertEqual(self.load_balancer.configuration_version, 2)
            self.assertEqual(self.load_balancer.deployed_configuration_version, 1)

    @patch("instance.ansible.poll_streams")
    @patch("instance.ansible.run_playbook")
    @patch('instance.models.load_balancer.LoadBalancingServer.get_instances', return_value=mock_instances())
    def test_deconfigure(self, mock_get_instances, mock_run_playbook, mock_poll_streams):
        """
        Test that the deconfigure() method triggers a playbook run.
        """
        mock_run_playbook.return_value.__enter__.return_value.returncode = 0
        self.load_balancer.deconfigure()
        #self.assertEqual(mock_run_playbook.call_count, 1)


class LoadBalancingServerManager(TestCase):
    """
    Tests for LoadBalancingServerManager.
    """
    @override_settings(DEFAULT_LOAD_BALANCING_SERVER=None)
    def test_no_load_balancer_available(self):
        """
        Test that get_random() raises an exception when no load balancers are available.
        """
        with self.assertRaises(LoadBalancingServer.DoesNotExist):
            LoadBalancingServer.objects.select_random()

    @override_settings(DEFAULT_LOAD_BALANCING_SERVER="domain.without.username")
    def test_invalid_default_load_balancer(self):
        """
        Verify that an exception gets raised when the username is missing from the setting for the
        default load balancing server.
        """
        with self.assertRaises(ImproperlyConfigured):
            LoadBalancingServer.objects.select_random()
