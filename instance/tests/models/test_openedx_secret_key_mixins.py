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
OpenEdXInstance secret key mixins - Tests
"""

# Imports #####################################################################

import codecs
import re
import yaml
import six

from instance.models.mixins.secret_keys import OPENEDX_SECRET_KEYS, OPENEDX_SHARED_KEYS
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.utils import patch_services


# Tests #######################################################################

class OpenEdXSecretKeyInstanceMixinTestCase(TestCase):
    """
    Test cases for SecretKeyInstanceMixin models
    """
    def test_secret_key_creation(self):
        """
        Test that we can reliably produce derived secret keys for an instance with a particular
        existing secret key.
        """
        instance = OpenEdXInstanceFactory()
        instance.secret_key_b64encoded = 'esFyh7kbvbMQiYhRx9fISJw9gkcSCStGAfOWaPu9cfc6/tMu'
        instance.save()

        self.assertEqual(
            instance.get_secret_key_for_var('THIS_IS_A_TEST'),
            '95652a974218e2efc44f99feb6f2ab89a263746688ff428ca2c898ae44111f58',
        )
        self.assertEqual(
            instance.get_secret_key_for_var('OTHER_TEST'),
            '820b455b1f0e30b75ec0514ab172c588223b010de3beacce3cd27217adc7fe60',
        )
        self.assertEqual(
            instance.get_secret_key_for_var('SUPER_SECRET'),
            '21b5271f21ee6dacfde05cd97e20739f0e73dc8a43408ef14b657bfbf718e2b4',
        )

    def test_secret_key_settings(self):
        """
        Test the YAML settings returned by SecretKeyInstanceMixin.
        """
        instance = OpenEdXInstanceFactory()
        secret_key_settings = yaml.load(instance.get_secret_key_settings())

        # Test that all keys are hex-encoded strings.
        for secret_key in secret_key_settings.values():
            codecs.decode(secret_key, "hex")

        # Make sure all independent secret keys are all different
        independent_secrets = set(secret_key_settings[var] for var in OPENEDX_SECRET_KEYS)
        self.assertEqual(len(independent_secrets), len(OPENEDX_SECRET_KEYS))

        # Verify that API client keys are set to the matching server key.
        for to_var, from_var in OPENEDX_SHARED_KEYS.items():
            self.assertEqual(secret_key_settings[to_var], secret_key_settings[from_var])

    def test_secret_key_settings_no_key(self):
        """
        Test that secret key settings are empty if the master key is not set.
        """
        instance = OpenEdXInstanceFactory()
        make_test_appserver(instance)
        instance.secret_key_b64encoded = ''
        instance.save()
        self.assertEqual(instance.get_secret_key_settings(), '')

    def test_http_auth_settings(self):
        """
        Test HTTP auth username and password generation.
        """
        instance = OpenEdXInstanceFactory()
        instance.secret_key_b64encoded = 'T3BlbkNyYWZ0'
        instance.save()

        self.assertEqual(instance.http_auth_user, '75182ee9f532ee81')
        self.assertEqual(instance.http_auth_pass, 'af350fc1d3ceb6c0')
        self.assertEqual(instance.http_auth_info_base64(), b'NzUxODJlZTlmNTMyZWU4MTphZjM1MGZjMWQzY2ViNmMw')

    @patch_services
    def test_do_not_create_insecure_secret_keys(self, mocks):
        """
        Test that if we have a brand-new instance with no appservers, we refuse to create insecure
        keys for those appservers if we don't have a secure secret key for the instance.
        """
        instance = OpenEdXInstanceFactory()
        instance.secret_key_b64encoded = ''
        instance.save()

        expected_error_string = re.escape(
            'Attempted to create secret key for instance {}, but no master key present.'.format(instance)
        )

        # Six provides a compatibility method for assertRaisesRegex, since the method
        # is named differently between Py2k and Py3k.
        with six.assertRaisesRegex(self, ValueError, expected_error_string):
            instance.spawn_appserver()
