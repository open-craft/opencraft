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

from django.test import TestCase

from instance.models.appserver import AppServer
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from marketing.models import Subscriber
from registration.approval import on_appserver_spawned
from registration.models import BetaTestApplication
from registration.tests.utils import BetaTestUserFactory


# Test cases ##################################################################


class RegisterSubscriberTestCase(TestCase):
    """
    Tests for the register_subscriber function
    """

    def test_trial_client_subscription(self):
        """
        Test new subscription entry for trial client on first successful launch of appserver
        """

        user = BetaTestUserFactory()

        instance = OpenEdXInstanceFactory()
        application = BetaTestApplication.objects.create(
            user=user,
            subdomain='test',
            instance=instance,
            instance_name='Test instance',
            project_description='Test instance creation.',
            public_contact_email=user.email,
            status=BetaTestApplication.PENDING
        )
        appserver = mock.Mock(status=AppServer.Status.Running)

        instance.betatestapplication.first = lambda: application
        application.instance = instance

        on_appserver_spawned(sender=None, instance=instance, appserver=appserver)
        self.assertTrue(Subscriber.objects.filter(user_id=application.user.id).exists())

    def test_existing_client_subscription(self):
        """
        Test no entry made in subscription table for paying clients on successful launch of appserver
        """

        user = BetaTestUserFactory()

        instance = OpenEdXInstanceFactory()
        application = BetaTestApplication.objects.create(
            user=user,
            subdomain='test',
            instance=instance,
            instance_name='Test instance',
            project_description='Test instance creation.',
            public_contact_email=user.email,
            status=BetaTestApplication.ACCEPTED
        )
        appserver = mock.Mock(status=AppServer.Status.Running)

        instance.betatestapplication.first = lambda: application
        application.instance = instance

        on_appserver_spawned(sender=None, instance=instance, appserver=appserver)
        self.assertFalse(Subscriber.objects.filter(user_id=application.user.id).exists())
