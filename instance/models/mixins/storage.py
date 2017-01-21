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

from django.conf import settings
from django.db import models
from swiftclient.exceptions import ClientException as SwiftClientException

from instance import openstack_utils


# Classes #####################################################################

class SwiftContainerInstanceMixin(models.Model):
    """
    Mixin to provision Swift containers for an instance.
    """
    swift_openstack_user = models.CharField(max_length=32, blank=True)
    swift_openstack_password = models.CharField(max_length=64, blank=True)
    swift_openstack_tenant = models.CharField(max_length=32, blank=True)
    swift_openstack_auth_url = models.URLField(blank=True)
    swift_openstack_region = models.CharField(max_length=16, blank=True)
    swift_provisioned = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def swift_container_names(self):
        """
        An iterable of Swift container names.
        """
        return NotImplementedError

    def provision_swift(self):
        """
        Create the Swift containers if necessary.
        """
        if settings.SWIFT_ENABLE:
            for container_name in self.swift_container_names:
                openstack_utils.create_swift_container(
                    container_name,
                    user=self.swift_openstack_user,
                    password=self.swift_openstack_password,
                    tenant=self.swift_openstack_tenant,
                    auth_url=self.swift_openstack_auth_url,
                    region=self.swift_openstack_region,
                )
            self.swift_provisioned = True
            self.save()

    def deprovision_swift(self):
        """
        Delete the Swift containers.
        """
        if settings.SWIFT_ENABLE and self.swift_provisioned:
            for container_name in self.swift_container_names:
                try:
                    openstack_utils.delete_swift_container(
                        container_name,
                        user=self.swift_openstack_user,
                        password=self.swift_openstack_password,
                        tenant=self.swift_openstack_tenant,
                        auth_url=self.swift_openstack_auth_url,
                        region=self.swift_openstack_region,
                    )
                except SwiftClientException:
                    # If deleting a Swift container fails, we still want to continue.
                    self.logger.exception('Could not delete Swift container "%s".', container_name)
            self.swift_provisioned = False
            self.save()
