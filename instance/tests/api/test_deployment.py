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
Views - Tests
"""

# Imports #####################################################################

from instance.models.deployment import DeploymentType
from instance.tests.api.base import APITestCase


# Tests #######################################################################

class DeploymentTypeAPITestCase(APITestCase):
    """
    Tests for the Deployment Type API
    """
    def test_deployment_type_list_contains_all_deployment_types(self):
        """
        GET - test DeploymentType API list
        """
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/deployment_type/').json()

        for deployment_type_json in response:
            deployment_type = DeploymentType[deployment_type_json['id']]
            self.assertEqual(deployment_type_json['id'], deployment_type.name)
            self.assertEqual(deployment_type_json['value'], deployment_type.value)

    def test_deployment_type_permission_login_required(self):
        """
        GET - test DeploymentType API available unavailable to logged in users
        """
        response = self.api_client.get(f'/api/v1/deployment_type/')
        self.assertEqual(response.status_code, 403)

    def test_deployment_type_permission_superuser_only(self):
        """
        GET - test DeploymentType API available to superusers
        """
        self.api_client.login(username='user1', password='pass')
        response = self.api_client.get(f'/api/v1/deployment_type/')
        self.assertEqual(response.status_code, 403)
