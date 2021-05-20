# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2020 OpenCraft <xavier@opencraft.com>
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
Test the domain verification utils
"""

# Imports #####################################################################
from unittest.mock import patch

import dns.resolver
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase

from registration.models import BetaTestApplication
from registration.utils import (
    is_dns_configured,
    is_external_domain_dns_configured,
    is_subdomain_dns_configured,
    send_dns_not_configured_email
)


# Test cases ##################################################################
class DomainUtilsTestCase(TestCase):
    """
    Tests the functions associated with domain configuration check
    """
    @patch('dns.resolver.resolve')
    def test_dns_configured(self, resolver_mock):
        """
        Tests that the function returns true if the DNS configuration
        has CNAME record with correct value
        """
        resolver_mock.return_value.__iter__.return_value = [settings.EXTERNAL_DOMAIN_CNAME_VALUE]
        is_passed = is_dns_configured('example.com')
        resolver_mock.assert_called_with('example.com', 'CNAME')
        self.assertTrue(is_passed)

    @patch('dns.resolver.resolve')
    def test_dns_not_configured(self, resolver_mock):
        """
        Tests that the configuration check fails if CNAME record is not present
        """
        # CNAME is present but the value is not correct
        resolver_mock.return_value.__iter__.return_value = ['to-random-domain.com']
        is_passed = is_dns_configured('example.com')
        resolver_mock.assert_called_with('example.com', 'CNAME')
        self.assertFalse(is_passed)

        # Returns False in cases where, record is not present, query doesn't
        # return an answer or all nameservers failed to answer the query.
        # Represented by following exceptions.
        resolver_mock.side_effect = [
            dns.resolver.NXDOMAIN,
            dns.resolver.NoAnswer,
            dns.resolver.NoNameservers
        ]
        self.assertFalse(is_dns_configured('example2.com'))
        self.assertFalse(is_dns_configured('example3.com'))
        self.assertFalse(is_dns_configured('example4.com'))

    @patch('registration.utils.is_dns_configured')
    def test_subdomain_configured(self, mock):
        """
        Tests that is_dns configured is called with prepended
        random subdomain for configuration check.
        Also tests it returns false when is_dns_configured returns false.
        """
        mock.return_value = True
        self.assertTrue(is_subdomain_dns_configured('example.com'))
        subdomain_1 = mock.call_args[0][0]
        self.assertTrue(subdomain_1.endswith('example.com'))
        self.assertGreater(len(subdomain_1), len('example.com'))

        mock.return_value = False
        self.assertFalse(is_subdomain_dns_configured('example.com'))
        subdomain_2 = mock.call_args[0][0]
        self.assertTrue(subdomain_2.endswith('example.com'))
        self.assertGreater(len(subdomain_2), len('example.com'))

        self.assertNotEqual(subdomain_1, subdomain_2)

    @patch('registration.utils.is_dns_configured')
    @patch('registration.utils.is_subdomain_dns_configured')
    def test_external_dns_configuration(self, mock_subdomain, mock_dns):
        """
        Tests that external_domain check calls both subdomain dns and base
        domain dns checks
        """
        mock_subdomain.return_value = True
        mock_dns.return_value = True

        self.assertTrue(is_external_domain_dns_configured('example.com'))
        mock_subdomain.assert_called_with('example.com')
        mock_dns.assert_called_with('example.com')

    @patch('registration.utils.html_email_helper')
    def test_dns_configuration_email(self, mock_email_helper):
        """
        Tests that sending dns configuration email uses proper template and context
        """
        user = get_user_model().objects.create_user(username='test', email='test@example.com')
        # Create application with BetaTestApplication.ACCEPTED status
        application = BetaTestApplication.objects.create(
            user=user,
            subdomain='test',
            external_domain="example.com",
            instance_name='Test instance',
            project_description='Test instance creation.',
            public_contact_email=user.email,
        )

        send_dns_not_configured_email(application)

        mock_email_helper.assert_called_with(
            template_base_name='emails/dns_not_configured',
            context={
                'cname_value': settings.EXTERNAL_DOMAIN_CNAME_VALUE,
                'external_domain': application.external_domain
            },
            subject='OpenCraft domain verification failed!',
            recipient_list=(user.email,)
        )
