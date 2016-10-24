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
LoadBalancingServer model - tests
"""
import re
from unittest.mock import patch, Mock

from instance.tests.base import TestCase
from instance.tests.models.factories.load_balancer import LoadBalancingServerFactory


def _make_mock_instance(domains, ip_address, backend_name):
    """
    Create a mock instance
    """
    instance = Mock()
    map_entries = [(domain, backend_name) for domain in domains]
    conf_entries = [(backend_name, "    server test-server {}:80".format(ip_address))]
    instance.get_load_balancer_configuration.return_value = map_entries, conf_entries
    return instance


class LoadBalancingServerTest(TestCase):
    """
    Test cases for the LoadBalancingServer model.
    """

    def test_get_configuration(self):
        """
        Test that the configuration gets rendered correctly.
        """
        load_balancer = LoadBalancingServerFactory()
        mock_instances = [
            _make_mock_instance(
                ["test1.lb.opencraft.hosting", "test2.lb.opencraft.hosting"],
                "1.2.3.4",
                "first-backend",
            ),
            _make_mock_instance(
                ["test3.lb.opencraft.hosting"],
                "5.6.7.8",
                "second-backend",
            ),
        ]
        with patch.object(load_balancer, "get_instances", return_value=mock_instances):
            backend_map, backend_conf = load_balancer.get_configuration()
            self.assertCountEqual(
                [line for line in backend_map.splitlines(False) if line],
                [
                    "test1.lb.opencraft.hosting first-backend" + load_balancer.fragment_name_postfix,
                    "test2.lb.opencraft.hosting first-backend" + load_balancer.fragment_name_postfix,
                    "test3.lb.opencraft.hosting second-backend" + load_balancer.fragment_name_postfix,
                ],
            )
            backends = [match.group(1) for match in re.finditer(r"^backend (\S*)", backend_conf, re.MULTILINE)]
            self.assertCountEqual(backends, [
                "first-backend" + load_balancer.fragment_name_postfix,
                "second-backend" + load_balancer.fragment_name_postfix,
            ])
