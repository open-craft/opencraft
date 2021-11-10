# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Tests for the register subscriber function
"""

# Imports #####################################################################

from unittest import mock
from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase


from instance.models.appserver import AppServer
from marketing.models import Subscriber
from userprofile.models import UserProfile
from registration.approval import on_appserver_spawned
from registration.models import BetaTestApplication


# Test cases ##################################################################


class RegisterSubscriberTestCase(TestCase):
    """
    Tests for the register_subscriber function
    """

    def test_trial_client_subscription(self):
        """
        Test new subscription entry for trial client on first successful launch of appserver
        """

        user = get_user_model().objects.create_user(username='test', email='test@example.com')

        UserProfile.objects.create(
            user=user,
            full_name="Test user 1",
            accepted_privacy_policy=datetime.now(),
            accept_domain_condition=True,
            subscribe_to_updates=True,
        )

        user.refresh_from_db()

        instance = mock.Mock(first_activated=None)
        application = mock.Mock(user=user, subdomain='test', status=BetaTestApplication.PENDING)
        appserver = mock.Mock(status=AppServer.Status.Running)

        instance.betatestapplication_set.first = lambda: application
        application.instance = instance

        on_appserver_spawned(sender=None, instance=instance, appserver=appserver)
        self.assertTrue(Subscriber.objects.filter(user_id=application.user.id).exists())

    def test_existing_client_subscription(self):
        """
        Test no entry made in subscription table for paying clients on successful launch of appserver
        """

        user = get_user_model().objects.create_user(username='test', email='test@example.com')

        UserProfile.objects.create(
            user=user,
            full_name="Test user 1",
            accepted_privacy_policy=datetime.now(),
            accept_domain_condition=True,
            subscribe_to_updates=True,
        )

        user.refresh_from_db()

        instance = mock.Mock(first_activated=None)
        application = mock.Mock(user=user, subdomain='test', status=BetaTestApplication.ACCEPTED)
        appserver = mock.Mock(status=AppServer.Status.Running)

        instance.betatestapplication_set.first = lambda: application
        application.instance = instance

        on_appserver_spawned(sender=None, instance=instance, appserver=appserver)
        self.assertFalse(Subscriber.objects.filter(user_id=application.user.id).exists())
