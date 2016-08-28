# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <xavier@opencraft.com>
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
Open edX instance database mixin
"""
from django.conf import settings
from django.db import models
from django.template import loader

from .storage import SwiftContainerInstanceMixin


# Classes #####################################################################

class OpenEdXStorageMixin(SwiftContainerInstanceMixin):
    """
    Mixin that provides functionality required for the storage backends that an OpenEdX
    Instance uses (when not using ephemeral databases)
    """
    class Meta:
        abstract = True

    s3_access_key = models.CharField(max_length=50, blank=True)
    s3_secret_access_key = models.CharField(max_length=50, blank=True)
    s3_bucket_name = models.CharField(max_length=50, blank=True)

    @property
    def swift_container_name(self):
        """
        The name of the Swift container used by the instance.
        """
        return self.database_name

    @property
    def swift_container_names(self):
        """
        The list of Swift container names to be created.
        """
        return [self.swift_container_name]

    def set_field_defaults(self):
        """
        Set default values for Swift credentials.

        Don't change existing values on subsequent calls.

        Credentials are only used for persistent databases (cf. get_storage_settings).
        We generate them for all instances to ensure that app servers can be spawned successfully
        even if an instance is edited to change 'use_ephemeral_databases' from True to False.
        """
        if settings.SWIFT_ENABLE and not self.swift_openstack_user:
            # TODO: Figure out a way to use separate credentials for each instance.  Access control
            # on Swift containers is granted to users, and there doesn't seem to be a way to create
            # Keystone users in OpenStack public clouds.
            self.swift_openstack_user = settings.SWIFT_OPENSTACK_USER
            self.swift_openstack_password = settings.SWIFT_OPENSTACK_PASSWORD
            self.swift_openstack_tenant = settings.SWIFT_OPENSTACK_TENANT
            self.swift_openstack_auth_url = settings.SWIFT_OPENSTACK_AUTH_URL
            self.swift_openstack_region = settings.SWIFT_OPENSTACK_REGION

    def get_storage_settings(self):
        """
        Get configuration_storage_settings to pass to a new AppServer

        Only needed when not using ephemeral databases
        """
        if self.use_ephemeral_databases:
            return ''

        new_settings = ''
        if self.s3_access_key and self.s3_secret_access_key and self.s3_bucket_name:
            # S3
            template = loader.get_template('instance/ansible/s3.yml')
            new_settings += template.render({'instance': self})
        elif settings.SWIFT_ENABLE:
            # Only enable Swift if S3 isn't configured
            template = loader.get_template('instance/ansible/swift.yml')
            new_settings += template.render({
                'user': self.swift_openstack_user,
                'password': self.swift_openstack_password,
                'tenant': self.swift_openstack_tenant,
                'auth_url': self.swift_openstack_auth_url,
                'region': self.swift_openstack_region,
                'container_name': self.swift_container_name,
            })
        return new_settings
