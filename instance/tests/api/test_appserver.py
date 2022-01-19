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

from instance.models.appserver import Status
from instance.tests.api.base import APITestCase


# Tests #######################################################################

class StatusAPITestCase(APITestCase):
    """
    Tests for the Status API
    """
    def test_status_list_contains_all_statuses(self):
        """
        GET - test Status API list
        """
        self.api_client.login(username='user3', password='pass')
        response = self.api_client.get('/api/v1/status/').json()

        for status_json in response:
            status = Status.states_with(state_id=status_json['id'])[0]
            self.assertEqual(status_json['id'], status.state_id)
            self.assertEqual(status_json['name'], status.name)

    def test_status_permission_login_required(self):
        """
        GET - test Status API available unavailable to logged in users
        """
        response = self.api_client.get(f'/api/v1/status/')
        self.assertEqual(response.status_code, 403)

    def test_status_permission_superuser_only(self):
        """
        GET - test Status API available to superusers
        """
        self.api_client.login(username='user1', password='pass')
        response = self.api_client.get(f'/api/v1/status/')
        self.assertEqual(response.status_code, 403)
