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
Instance app model mixins - Database
"""

# Imports #####################################################################

import os
import hashlib
import hmac
from base64 import b64encode, b64decode

from django.db import models
from django.template import loader

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


# Classes #####################################################################

class SecretKeyInstanceMixin(models.Model):
    """
    An instance that needs to generate a set of secret keys for different purposes
    """
    secret_key_b64encoded = models.CharField(
        max_length=48,
        blank=True,
        verbose_name='Instance-specific base-64-encoded secret key',
        help_text=(
            "This field holds a base-64-encoded secret key that is generated "
            "when the instance is created, and is used to generate secret keys "
            "for individual services on each appserver."
        ),
    )

    class Meta:
        abstract = True

    def set_random_key(self):
        """
        Generates a random seed for this instance to use when creating
        derived secret keys for instance variables
        """
        self.secret_key_b64encoded = generate_secret_key(48)

    def get_secret_key_settings(self):
        """
        Render the secret keys template as YAML and return it for use
        in the appserver.
        """
        key_provider = self.get_key_provider()
        if not self.secret_key_b64encoded:
            self.logger.warning('Instance does not have a secret key; not prefilling variables.')
            return ''
        template = loader.get_template('instance/ansible/secret-keys.yml')
        return template.render({"secret_generator": key_provider})

    def get_key_provider(self):
        """
        Get a proxy we can pass to a template that'll generate secret keys
        for any attribute requested from it.
        """
        if not self.appserver_set.exists() and not self.secret_key_b64encoded:
            raise ValueError(
                'Attempted to create key provider for instance {}, but no key present.'.format(self)
            )
        return SecretKeyProvider(self.secret_key_b64encoded)


class SecretKeyProvider:
    """
    Proxy object that, when an attribute is requested from it, will provide
    a unique secret key generated based on the name of the attribute.
    """
    def __init__(self, secret_key):
        """
        Save the secret key
        """
        self.secret_key = b64decode(secret_key)

    def __getattr__(self, var_name):
        """
        Create an HMAC that can be used as a secret key, based on the variable
        name that was requested.
        """
        return hmac.new(self.secret_key, msg=var_name.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()
