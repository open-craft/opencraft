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
Tests for the betatest approval helper functions
"""

# Imports #####################################################################

from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from registration.approval import accept_application, ApplicationNotReady, on_appserver_spawned
from registration.models import BetaTestApplication
from instance.models.appserver import AppServer

# Test cases ##################################################################
# pylint: disable=no-self-use


class ApprovalTestCase(TestCase):
    """Tests for the helper functions in the approval module."""

    def test_no_appserver(self):
        """ Make sure it fails without an AppServer """
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        application = mock.Mock(user=user, subdomain='test')

        # Test failure when no appserver is given
        with self.assertRaises(ApplicationNotReady):
            accept_application(application, None)

    def test_appserver_not_running(self):
        """ Make sure it fails when the AppServer isn't running """
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        application = mock.Mock(user=user, subdomain='test')

        # Test failure when appserver isn't running
        appserver = mock.Mock(status=AppServer.Status.Terminated)
        with self.assertRaises(ApplicationNotReady):
            accept_application(application, appserver)

    def test_accept_application(self):
        """ Make sure email is sent in case of success """
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        application = mock.Mock(user=user, subdomain='test')
        appserver = mock.Mock(status=AppServer.Status.Terminated)

        # Test email is sent when everything is correct
        appserver.status = AppServer.Status.Running
        with mock.patch('registration.approval._send_mail') as mock_send_mail:
            accept_application(application, appserver)
            mock_send_mail.assert_called_once_with(
                application,
                'registration/welcome_email.txt',
                settings.BETATEST_WELCOME_SUBJECT
            )
        self.assertEqual(application.status, BetaTestApplication.ACCEPTED)

    def test_no_application(self):
        """ Basic test for appserver_spawned() without an application """

        appserver = mock.Mock()
        instance = mock.Mock()
        instance.betatestapplication_set.first = lambda: None

        # Test nothing happens without an application
        with mock.patch('registration.approval.accept_application') as mock_application:
            on_appserver_spawned(sender=None, instance=instance, appserver=appserver)
            mock_application.assert_not_called()

    def test_accepted_application(self):
        """ Basic test for appserver_spawned() with ACCEPTED application """

        appserver = mock.Mock()
        instance = mock.Mock()
        application = mock.Mock(status=BetaTestApplication.ACCEPTED)
        instance.betatestapplication_set.first = lambda: application

        # Test accepted application does nothing
        with mock.patch('registration.approval.accept_application') as mock_application:
            on_appserver_spawned(sender=None, instance=instance, appserver=appserver)
            mock_application.assert_not_called()

    def test_pending_application(self):
        """ Basic test for appserver_spawned() success """

        appserver = mock.Mock()
        instance = mock.Mock()
        application = mock.Mock(status=BetaTestApplication.PENDING)
        instance.betatestapplication_set.first = lambda: application

        # Test accepted application does nothing
        with mock.patch('registration.approval.accept_application') as mock_application:
            on_appserver_spawned(sender=None, instance=instance, appserver=appserver)
            self.assertEqual(mock_application.call_count, 1)

    def test_appserver_spawned(self):
        """ Basic test for appserver_spawned() failure and success behaviour """

        instance = mock.Mock()
        application = mock.Mock(status=BetaTestApplication.PENDING)
        instance.betatestapplication_set.first = lambda: application

        # Test failed spawning generates an exception in case of pending application
        with mock.patch('registration.approval.accept_application') as mock_application:
            with self.assertRaises(ApplicationNotReady):
                on_appserver_spawned(sender=None, instance=instance, appserver=None)
            mock_application.assert_not_called()

    def test_first_appserver_is_active(self):
        """
        Check if the the first Appserver is correctly activated even when
        spawned manually
        """
        appserver = mock.Mock(status=AppServer.Status.Running)
        instance = mock.Mock(first_activated=None)
        application = mock.Mock(status=BetaTestApplication.PENDING)

        application.instance = instance
        instance.betatestapplication_set.first = lambda: application

        # Test accepted application does nothing
        on_appserver_spawned(sender=None, instance=instance, appserver=appserver)
        self.assertEqual(appserver.make_active.call_count, 1)
