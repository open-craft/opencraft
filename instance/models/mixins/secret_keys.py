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
Instance app model mixins - Database
"""

# Imports #####################################################################

import functools
import os
import hashlib
import hmac
import json
from base64 import b64encode, b64decode
from collections import namedtuple
from Cryptodome.PublicKey import RSA
from jwkest import jwk

from django.db import models
import yaml

# Functions ###################################################################


def generate_secret_key(char_length):
    """
    Creates a base64-encoded string of character length `char_length`
    for use in other functions.
    """
    if char_length <= 0 or char_length % 4:
        # b64encode will always pad its output to four characters, regardless
        # of the byte count. We'd rather error out than encode too few or too many.
        raise ValueError('char_length must be a positive multiple of 4')
    # We need three random bytes per four random b64 characters.
    random_bytes = os.urandom(int(char_length * 0.75))
    # Encode to a b64 string...
    random_string = b64encode(random_bytes)
    # ...and return!
    return random_string


def generate_rsa_key(key_size):
    """
    Creates a key_size-bit RSA key and returns private key
    """
    rsa_key = RSA.generate(key_size)
    return rsa_key.exportKey()


# Constants ###################################################################

# The names of Ansible variables that should be set to independent random keys.
OPENEDX_SECRET_KEYS = [
    'ANALYTICS_API_SECRET_KEY',
    'CREDENTIALS_SECRET_KEY',
    'DISCOVERY_SECRET_KEY',
    'DISCOVERY_SOCIAL_AUTH_EDX_OIDC_KEY',
    'DISCOVERY_SOCIAL_AUTH_EDX_OIDC_SECRET',
    'ECOMMERCE_CYBERSOURCE_SECRET_KEY',
    'ECOMMERCE_SECRET_KEY',
    'ECOMMERCE_SOCIAL_AUTH_EDX_OIDC_KEY',
    'ECOMMERCE_SOCIAL_AUTH_EDX_OIDC_SECRET',
    'ECOMMERCE_WORKER_JWT_SECRET_KEY',
    'EDXAPP_ANALYTICS_API_KEY',
    'EDXAPP_EDXAPP_SECRET_KEY',
    'EDXAPP_EDX_API_KEY',
    'EDXAPP_JWT_SECRET_KEY',
    'EDXAPP_PROFILE_IMAGE_SECRET_KEY',
    'EDX_NOTES_API_SECRET_KEY',
    'FORUM_API_KEY',
    'INSIGHTS_SECRET_KEY',
    'NOTIFIER_LMS_SECRET_KEY',
    'PROGRAMS_SECRET_KEY',
    'RETIREMENT_SERVICE_OAUTH_CLIENT_ID',
    'RETIREMENT_SERVICE_OAUTH_CLIENT_SECRET',
]

# Translation table for keys that must match other keys (shared API keys)
OPENEDX_SHARED_KEYS = {
    'ECOMMERCE_EDX_API_KEY': 'EDXAPP_EDX_API_KEY',
    'EDXAPP_COMMENTS_SERVICE_KEY': 'FORUM_API_KEY',
    'NOTIFIER_COMMENT_SERVICE_API_KEY': 'FORUM_API_KEY',
    'NOTIFIER_USER_SERVICE_API_KEY': 'EDXAPP_EDX_API_KEY',
}


# Classes #####################################################################

class SecretKeyInstanceMixin(models.Model):
    """
    An instance that needs to generate a set of secret keys for different purposes
    """
    secret_key_b64encoded = models.CharField(
        max_length=48,
        default=functools.partial(generate_secret_key, 48),
        blank=True,
        verbose_name='Instance-specific base-64-encoded secret key',
        help_text=(
            "This field holds a base-64-encoded secret key that is generated "
            "when the instance is created, and is used to generate secret keys "
            "for individual services on each appserver."
        ),
    )

    secret_key_rsa_private = models.TextField(
        default=functools.partial(generate_rsa_key, 2048),
        blank=True,
        verbose_name='Instance-specific private RSA key',
        help_text=(
            "This field holds a RSA private key that is generated "
            "when the instance is created, and is used to generate public "
            "and private JWK for individual services on each appserver."
        ),
    )

    class Meta:
        abstract = True

    @property
    def secret_key(self):
        """
        Return the secret key in binary form.
        """
        return b64decode(self.secret_key_b64encoded)

    @property
    def rsa_key(self):
        """
        Return the RSA key as a Cryptodome.RSA object.
        """
        if not self.secret_key_rsa_private:
            self.secret_key_rsa_private = generate_rsa_key(2048)
            self.save()

        return RSA.importKey(self.secret_key_rsa_private)

    def get_secret_key_for_var(self, var_name):
        """
        Return the secret key for the given variable name.
        """
        return hmac.new(self.secret_key, msg=var_name.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

    def get_jwk_key_pair(self):
        """
        Returns the asymmetric JWT signing keys required
        """
        rsa_jwk = jwk.RSAKey(kid="opencraft", key=self.rsa_key)

        # Serialize public JWT signing keys
        public_keys = jwk.KEYS()
        public_keys.append(rsa_jwk)
        serialized_public_keys_json = public_keys.dump_jwks()

        # Serialize private JWT signing keys
        serialized_keypair = rsa_jwk.serialize(private=True)
        serialized_keypair_json = json.dumps(serialized_keypair)

        # Named tuple for storing public and private JWT key pair
        jwk_key_pair = namedtuple('JWK_KEY_PAIR', ['public', 'private'])
        jwk_key_pair.public = serialized_public_keys_json
        jwk_key_pair.private = serialized_keypair_json

        return jwk_key_pair

    def get_secret_key_settings(self):
        """
        Render the secret key settings as YAML and return it for use in the appserver.
        """
        if not self.secret_key_b64encoded:
            if not self.appserver_set.exists():
                raise ValueError(
                    'Attempted to create secret key for instance {}, but no master key present.'.format(self)
                )
            self.logger.warning('Instance does not have a secret key; not prefilling variables.')
            return ''
        keys = {var: self.get_secret_key_for_var(var) for var in OPENEDX_SECRET_KEYS}
        for to_var, from_var in OPENEDX_SHARED_KEYS.items():
            keys[to_var] = keys[from_var]

        # Add JWK key pair to dict
        jwk_key_pair = self.get_jwk_key_pair()
        keys['COMMON_JWT_PUBLIC_SIGNING_JWK_SET'] = jwk_key_pair.public
        keys['EDXAPP_JWT_PRIVATE_SIGNING_JWK'] = jwk_key_pair.private

        return yaml.dump(keys)

    @property
    def http_auth_user(self):
        """
        Return the HTTP basic auth user name.
        """
        return self.get_secret_key_for_var('COMMON_HTPASSWD_USER')[:16]

    @property
    def http_auth_pass(self):
        """
        Return the HTTP basic auth password.
        """
        return self.get_secret_key_for_var('COMMON_HTPASSWD_PASS')[:16]

    def http_auth_info_base64(self):
        """
        Return the HTTP auth information in the format required by Authorization HTTP header.
        """
        user_pass = '{}:{}'.format(self.http_auth_user, self.http_auth_pass)
        return b64encode(user_pass.encode('latin1'))
