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
Views - Index - Tests
"""

# Imports #####################################################################

from django.conf import settings
from django.core.urlresolvers import reverse

from instance.tests.base import WithUserTestCase


# Tests #######################################################################

class IndexViewsTestCase(WithUserTestCase):
    """
    Test cases for views
    """
    url = reverse('instance:index')
    login_url = reverse(settings.LOGIN_URL)
    register_url = reverse('registration:register')

    def test_index_unauthenticated(self):
        """
        Index view - Unauthenticated users go to login page
        """
        response = self.client.get(self.url)
        self.assertRedirects(response,
                             '{0}?next={1}'.format(self.login_url, self.url))

    def test_index_authenticated_basic_user(self):
        """
        Index view - Authenticated, unprivileged user
        """
        self.client.login(username='user1', password='pass')
        response = self.client.get(self.url)
        self.assertRedirects(response, self.register_url)

    def test_index_authenticated_staff(self):
        """
        Index view - Authenticated, staff user
        """
        self.client.login(username='user2', password='pass')
        response = self.client.get(self.url)
        self.assertRedirects(response, self.register_url)

    def test_index_authenticated_instance_manager(self):
        """
        Index view - Authenticated, instance manager user
        """
        self.client.login(username='user3', password='pass')
        response = self.client.get(self.url)
        self.assertContains(response, 'ng-app="InstanceApp"')
