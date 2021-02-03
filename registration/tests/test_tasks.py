# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <contact@opencraft.com>
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
Worker tasks - Tests
"""
from unittest.mock import patch

from django.test import TestCase

from instance.tests.base import create_user_and_profile
from registration.models import BetaTestApplication, DNSConfigState
from registration.tasks import verify_external_domain_configuration


class VerifyExternalDomainTestCase(TestCase):
    """
    Test cases for tasks.verify_external_domain_configuration
    """
    def setUp(self):
        self.user1 = create_user_and_profile("instance.user1", "instance.user@example.com")
        self.user2 = create_user_and_profile("instance.user2", "instance.user@example.com")
        self.app_with_external_domain = BetaTestApplication.objects.create(
            user=self.user1,
            subdomain="somesubdomain",
            external_domain="externaldomain.com",
            dns_configuration_state=DNSConfigState.pending,
            instance_name="User's Instance",
            public_contact_email="instance.user1.public@example.com",
            privacy_policy_url="http://www.some/url"
        )
        self.app_without_external_domain = BetaTestApplication.objects.create(
            user=self.user2,
            subdomain="somesubdomain2",
            instance_name="User's Instance",
            public_contact_email="instance.user2.public@example.com",
            privacy_policy_url="http://www.some/url"
        )

    def _reset_state(self):
        """
        Reset the application dns_configuration_state to pending
        """
        self.app_with_external_domain.dns_configuration_state = DNSConfigState.pending
        self.app_with_external_domain.save()

    @patch('registration.tasks.is_external_domain_dns_configured', return_value=True)
    def test_state_to_verified_if_configured(self, mock_verify):
        """
        Tests that the dns_configuration is set to DNSConfigState.verified if
        the configuration is correct. Also check that verification is not
        called again if tasks is run.
        """
        verify_external_domain_configuration(self.app_with_external_domain.pk)

        application = BetaTestApplication.objects.get(pk=self.app_with_external_domain.pk)
        mock_verify.assert_called_once_with(application.external_domain)
        self.assertEqual(application.dns_configuration_state, DNSConfigState.verified.name)

        verify_external_domain_configuration(self.app_with_external_domain.pk)
        self.assertEqual(mock_verify.call_count, 1)

        self._reset_state()

    @patch('registration.tasks.is_external_domain_dns_configured', return_value=False)
    def test_state_to_failed_if_not_configured(self, mock_verify):
        """
        Tests that the dns_configuration_state is set to DNSConfigState.failed if
        the configuration is not correct. Also check that verification is not
        called again if tasks is run.
        """
        verify_external_domain_configuration(self.app_with_external_domain.pk)

        application = BetaTestApplication.objects.get(pk=self.app_with_external_domain.pk)
        mock_verify.assert_called_once_with(application.external_domain)
        self.assertEqual(application.dns_configuration_state, DNSConfigState.failed.name)

        verify_external_domain_configuration(self.app_with_external_domain.pk)
        self.assertEqual(mock_verify.call_count, 1)

        self._reset_state()

    @patch('registration.tasks.is_external_domain_dns_configured', return_value=True)
    def test_not_called_for_no_external_domain(self, mock_verify):
        """
        Test that the verification is not run if external domain is not
        present.
        """
        verify_external_domain_configuration(self.app_without_external_domain.pk)

        application = BetaTestApplication.objects.get(pk=self.app_without_external_domain.pk)
        mock_verify.assert_not_called()
        self.assertEqual(application.dns_configuration_state, DNSConfigState.not_required.name)
