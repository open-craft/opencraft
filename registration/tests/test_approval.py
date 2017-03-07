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
Tests for the betatest approval helper functions
"""

# Imports #####################################################################

from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from registration.approval import accept_application
from registration.models import BetaTestApplication
from instance.models.appserver import AppServer

# Test cases ##################################################################


class ApprovalTestCase(TestCase):
    """Tests for the helper functions in the approval module."""

    def test_accept_application(self):
        """Basic test for accept_application(), mainly for coverage."""
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        application = mock.Mock(user=user, subdomain='test')
        application.instance.active_appserver.status = AppServer.Status.Running
        with mock.patch('registration.approval.send_mail') as mock_send_mail:
            accept_application(application)
            self.assertTrue(mock_send_mail.called)
        self.assertEqual(application.status, BetaTestApplication.ACCEPTED)

    # TODO: Test error cases
