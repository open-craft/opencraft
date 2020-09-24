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
from unittest.mock import patch

import ddt
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from instance.factories import instance_factory
from instance.tests.base import create_user_and_profile
from registration.models import (
    BetaTestApplication,
    validate_available_external_domain,
    validate_available_subdomain,
    validate_subdomain_is_not_blacklisted,
)


@ddt.ddt
class ValidatorTestCase(TestCase):
    """
    Test case for validators used for models, but not strictly as a models field validator.
    """

    def setUp(self):
        self.user_with_instance = create_user_and_profile('instance.user', 'instance.user@example.com')
        self.existing_instance_config = BetaTestApplication.objects.create(
            user=self.user_with_instance,
            subdomain='somesubdomain',
            instance_name="User's Instance",
            public_contact_email='instance.user.public@example.com',
            privacy_policy_url='http://www.some/url'
        )

    @override_settings(SUBDOMAIN_BLACKLIST=['otherdomain'])
    def test_subdomain_is_not_blacklisted(self):
        """
        Validate that a blacklisted subdomain raises validation error.
        """
        subdomain = 'newsubdomain'
        validate_subdomain_is_not_blacklisted(subdomain)

    @override_settings(SUBDOMAIN_BLACKLIST=['newsubdomain'])
    def test_subdomain_is_blacklisted(self):
        """
        Validate that a blacklisted subdomain raises validation error.
        """
        subdomain = 'newsubdomain'

        with self.assertRaises(ValidationError) as exc:
            validate_subdomain_is_not_blacklisted(subdomain)

        self.assertEqual(exc.exception.message, 'This domain name is not publicly available.')
        self.assertEqual(exc.exception.code, 'blacklisted')

    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='example.com', GANDI_DEFAULT_BASE_DOMAIN='example.com')
    @patch('registration.models.gandi_api')
    def test_validate_available_subdomain(self, mock_gandi_api):
        """
        Validate that a correct subdomain does not cause a validation error.
        """
        subdomain = 'newsubdomain'
        internal_domains = ['some', 'internal', 'domain']
        mock_gandi_api.filter_dns_records.return_value = [
            {'content': f'{domain}.example.com'} for domain in internal_domains
        ]

        validate_available_subdomain(subdomain)

        mock_gandi_api.filter_dns_records.assert_called_once_with(settings.DEFAULT_INSTANCE_BASE_DOMAIN)

    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='example.com', GANDI_DEFAULT_BASE_DOMAIN='example.com')
    @patch('registration.models.gandi_api')
    def test_subdomain_is_taken(self, mock_gandi_api):
        """
        Validate that a taken subdomain raises validation error.
        """
        subdomain = 'newsubdomain'
        mock_gandi_api.filter_dns_records.return_value = [
            {'content': f'{subdomain}.example.com'}
        ]

        with self.assertRaises(ValidationError) as exc:
            validate_available_subdomain(subdomain)

        self.assertEqual(exc.exception.message, 'This domain is already taken.')
        self.assertEqual(exc.exception.code, 'unique')
        mock_gandi_api.filter_dns_records.assert_called_once_with(settings.DEFAULT_INSTANCE_BASE_DOMAIN)

    @override_settings(DEFAULT_INSTANCE_BASE_DOMAIN='example.com', GANDI_DEFAULT_BASE_DOMAIN='example.com')
    @patch('registration.models.gandi_api')
    def test_subdomain_cannot_be_validated(self, mock_gandi_api):
        """
        Validate validation error raised when we cannot check the domain's DNS records.

        It is better to raise an error to the user then mess up our domains.
        """
        subdomain = 'newsubdomain'
        mock_gandi_api.filter_dns_records.side_effect = ValueError()

        with self.assertRaises(ValidationError) as exc:
            validate_available_subdomain(subdomain)

        self.assertEqual(exc.exception.message, 'The domain cannot be validated.')
        self.assertEqual(exc.exception.code, 'cannot_validate')
        mock_gandi_api.filter_dns_records.assert_called_once_with(settings.DEFAULT_INSTANCE_BASE_DOMAIN)

    @patch('registration.models.gandi_api')
    @ddt.data(
        ("studio", 'Cannot register domain starting with "studio".'),
        ("preview", 'Cannot register domain starting with "preview".'),
        ("discovery", 'Cannot register domain starting with "discovery".'),
        ("ecommerce", 'Cannot register domain starting with "ecommerce".'),
    )
    @ddt.unpack
    def test_external_domain_subdomain_is_reserved(self, domain, error_message, mock_gandi_api):
        """
        Validate that the user cannot register a reserved subdomain.
        """
        with self.assertRaises(ValidationError) as exc:
            validate_available_subdomain(domain)

        self.assertEqual(exc.exception.message, error_message)
        self.assertEqual(exc.exception.code, 'reserved')
        self.assertFalse(mock_gandi_api.filter_dns_records.called)

    @patch('registration.models.gandi_api')
    def test_validate_available_external_domain(self, mock_gandi_api):
        """
        Validate that a correct external domain does not cause a test_external_domain_subdomain_is_reserved
        validation error.
        """
        domain = 'domain'

        validate_available_external_domain(domain)

        self.assertFalse(mock_gandi_api.filter_dns_records.called)

    @patch('registration.models.gandi_api')
    def test_external_domain_is_the_base_domain(self, mock_gandi_api):
        """
        Validate that the base domain cannot be used for external domain
        """
        domain = settings.DEFAULT_INSTANCE_BASE_DOMAIN

        with self.assertRaises(ValidationError) as exc:
            validate_available_external_domain(domain)

        self.assertEqual(exc.exception.message, f'The domain "{domain}" is not allowed.')
        self.assertEqual(exc.exception.code, 'reserved')

    @ddt.data(
        ('mydomain.com', 'mydomain.com'),
        ('mydomain.com', 'preview.mydomain.com'),
        ('mydomain.com', 'studio.mydomain.com'),
        ('mydomain.com', 'preview.mydomain.com'),
        ('mydomain.com', 'discovery.mydomain.com'),
        ('mydomain.com', 'ecommerce.mydomain.com'),
        ('mydomain.com', 'subdomain-of.mydomain.com'),
        ('mydomain.com', 'sub.domain.of.mydomain.com'),
        ('subdomain-of.mydomain.com', 'mydomain.com'),
        ('sub.domain.of.mydomain.com', 'mydomain.com'),
    )
    @ddt.unpack
    def test_external_domain_already_registered(self, new_domain, registered_domain):
        """
        Validate that the user cannot register a subdomain for an already registered domain.
        """
        instance_factory(
            sub_domain=registered_domain.split(".")[0],
            external_lms_domain=registered_domain
        )

        with self.assertRaises(ValidationError) as exc:
            validate_available_external_domain(new_domain)

        self.assertEqual(exc.exception.message, 'This domain is already taken.')
        self.assertEqual(exc.exception.code, 'unique')

    @ddt.data(
        ("studio.mydomain.com", 'Cannot register domain starting with "studio".'),
        ("preview.mydomain.com", 'Cannot register domain starting with "preview".'),
        ("discovery.mydomain.com", 'Cannot register domain starting with "discovery".'),
        ("ecommerce.mydomain.com", 'Cannot register domain starting with "ecommerce".'),
    )
    @ddt.unpack
    def test_external_domain_is_reserved(self, domain, error_message):
        """
        Validate that the user cannot register a reserved subdomain.
        """
        with self.assertRaises(ValidationError) as exc:
            validate_available_external_domain(domain)

        self.assertEqual(exc.exception.message, error_message)
        self.assertEqual(exc.exception.code, 'reserved')
