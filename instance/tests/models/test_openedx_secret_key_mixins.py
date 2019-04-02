# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
import json
import re
import yaml
import six
from Cryptodome.PublicKey import RSA

from instance.models.mixins.secret_keys import OPENEDX_SECRET_KEYS, OPENEDX_SHARED_KEYS
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.utils import patch_services


# Constants ####################################################################


JWK_SET_KEY_NAMES = [
    'COMMON_JWT_PUBLIC_SIGNING_JWK_SET',
    'EDXAPP_JWT_PRIVATE_SIGNING_JWK'
]


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

        # Test that all keys are hex-encoded strings,
        # except for the JWK keys, wich must be valid JSON strings
        for secret_key_name in secret_key_settings.keys():
            if secret_key_name not in JWK_SET_KEY_NAMES:
                codecs.decode(
                    secret_key_settings[secret_key_name],
                    "hex"
                )
            else:
                json.loads(secret_key_settings[secret_key_name])

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

    def test_rsa_key_creation(self):
        """
        Test that we can produce public and private key pair for an
        instance with a particular existing secret key.
        """
        instance = OpenEdXInstanceFactory()
        instance.secret_key_rsa_private = """-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQDEXX4rFLFl/eT3NJD8Y8rDcS39ynIjdYxaOHx6Q+PszU4YR6M0
3k3oMyDboIju6R8zim2JR9FWlOZTNN1MVSPOvu51CD4igNh5o+mgeBhVc+eatbvC
boDDtk/kHO0DEyebzO8oIortnh2pXF+Oyu3MdcyMFeF5xVEKqD0HQ9d05QIDAQAB
AoGAVDl9umC/zm1eXiHv5jGvcLEE9wx0dH0g3DnKOm8QPiu5SXTArhaD+AqmF03+
LetT9Ll1TiK9yZNIT3wnR2xlVLH6VuwcZ07KMUtvYLiuVGIAVf1TLs2E3zxRcrHb
TMsg15QnMFsat9yqMXSNPbqrs9tHU4hBv1k3uvkB4KWJVakCQQDjBYPaxmo8jyyJ
QzdLDh/cv20t4Q5LGB/XbfHTfJmnamToto6hEfG3Coy3/bbYhwFrWK53iKQpvkzg
vxNMlQoLAkEA3W4093Nai0V+YHVzI3fGqciSYrR4klYACqnIb+OlmLaT+Zj3Uv+d
P9BDy7frzRX9hYPQXMhYVxQBZtcF/CjCzwJADYUjkCDm7MpeDaKqJVcnAJ+J4gSY
NFKwesT6dOzjvbuxXMaage8upQcE0GRUwlpv9DOo2EeT90R1EaFvhc0OdwJAK7eV
d4Frz/FheRPXLpp4O48g76Hn6CRYj8Jjk0ujpxns7yt3MQjMeAvbRr5CLNR5oEGd
AqR/ZHnLqQ0s3lMB2wJAM3JaM2LtR3XhvQqT2vBteGB+iIWSh8cSxfWcd/vVSKIk
yF9iraiA2UvfpdwQSgXWsm7/+70kzVsb/MGl3rn63A==
-----END RSA PRIVATE KEY-----"""
        instance.save()

        jwk_key_pair = instance.get_jwk_key_pair()

        self.assertEqual(
            json.loads(jwk_key_pair.private),
            {
                "n": "xF1-KxSxZf3k9zSQ_GPKw3Et_cpyI3WMWjh8ekPj7M1OGEejNN5N6DMg"
                     "26CI7ukfM4ptiUfRVpTmUzTdTFUjzr7udQg-IoDYeaPpoHgYVXPnmrW7"
                     "wm6Aw7ZP5BztAxMnm8zvKCKK7Z4dqVxfjsrtzHXMjBXhecVRCqg9B0PX"
                     "dOU",
                "kid": "opencraft",
                "kty": "RSA",
                "d": "VDl9umC_zm1eXiHv5jGvcLEE9wx0dH0g3DnKOm8QPiu5SXTArhaD-Aqm"
                     "F03-LetT9Ll1TiK9yZNIT3wnR2xlVLH6VuwcZ07KMUtvYLiuVGIAVf1T"
                     "Ls2E3zxRcrHbTMsg15QnMFsat9yqMXSNPbqrs9tHU4hBv1k3uvkB4KWJ"
                     "Vak",
                "p": "4wWD2sZqPI8siUM3Sw4f3L9tLeEOSxgf123x03yZp2pk6LaOoRHxtwqM"
                     "t_222IcBa1iud4ikKb5M4L8TTJUKCw",
                "q": "3W4093Nai0V-YHVzI3fGqciSYrR4klYACqnIb-OlmLaT-Zj3Uv-dP9BD"
                     "y7frzRX9hYPQXMhYVxQBZtcF_CjCzw",
                "e": "AQAB"
            }
        )
        self.assertEqual(
            json.loads(jwk_key_pair.public),
            {
                "keys": [{
                    "e": "AQAB",
                    "kty": "RSA",
                    "kid": "opencraft",
                    "n": "xF1-KxSxZf3k9zSQ_GPKw3Et_cpyI3WMWjh8ekPj7M1OGEejNN5N"
                         "6DMg26CI7ukfM4ptiUfRVpTmUzTdTFUjzr7udQg-IoDYeaPpoHgY"
                         "VXPnmrW7wm6Aw7ZP5BztAxMnm8zvKCKK7Z4dqVxfjsrtzHXMjBXh"
                         "ecVRCqg9B0PXdOU"
                }]
            },
        )

    def test_get_generate_rsa_if_empty(self):
        """
        Test if a RSA key is generated when it's request if theres no RSA keys
        stored
        """
        instance = OpenEdXInstanceFactory()
        instance.secret_key_rsa_private = ""
        instance.save()

        rsa_key = instance.rsa_key
        self.assertTrue(bool(rsa_key))
        self.assertTrue(isinstance(rsa_key, RSA.RsaKey))

        instance.refresh_from_db()

        self.assertIsNotNone(instance.secret_key_rsa_private)
