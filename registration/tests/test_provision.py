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
Test the provisioning of beta tester instances.
"""

# Imports #####################################################################

from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from freezegun import freeze_time
from pytz import utc
from simple_email_confirmation.models import EmailAddress

from registration.models import BetaTestApplication

# Test cases ##################################################################


class ApprovalTestCase(TestCase):
    """Test the provisioning of beta tester instances."""

    def test_provision_instance(self):
        """Test that an instance gets correctly provisioned when the email addresses are confirmed."""
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        with freeze_time('2019-01-02 09:30:00') as frozen_time:
            accepted_time = utc.localize(frozen_time())
            accepted_time = accepted_time.strftime('%Y-%m-%d %H:%M:%S%z')
            application = BetaTestApplication.objects.create(
                user=user,
                subdomain='test',
                instance_name='Test instance',
                project_description='Test instance creation.',
                public_contact_email=user.email,
                accepted_privacy_policy=accepted_time
            )
        EmailAddress.objects.create_unconfirmed(user.email, user)
        with mock.patch('registration.provision.spawn_appserver') as mock_spawn_appserver:
            # Confirm email address.  This triggers provisioning the instance.
            EmailAddress.objects.confirm(user.email_address_set.get().key)
            self.assertTrue(mock_spawn_appserver.called)
        application.refresh_from_db()
        instance = application.instance
        self.assertIsNot(instance, None)
        self.assertTrue(instance.internal_lms_domain.startswith(application.subdomain))
        self.assertEqual(instance.email, application.public_contact_email)
        self.assertEqual(instance.lms_users.get(), user)
