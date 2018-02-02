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
import yaml

from django.conf import settings
from django.db import models

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

    def _get_s3_settings(self):
        """
        Return dictionary of S3 Ansible settings.
        """
        return {
            "COMMON_ENABLE_AWS_INTEGRATION": True,
            "AWS_ACCESS_KEY_ID": self.s3_access_key,
            "AWS_SECRET_ACCESS_KEY": self.s3_secret_access_key,

            "EDXAPP_DEFAULT_FILE_STORAGE": 'storages.backends.s3boto3.S3Boto3Storage',
            "EDXAPP_AWS_ACCESS_KEY_ID": self.s3_access_key,
            "EDXAPP_AWS_SECRET_ACCESS_KEY": self.s3_secret_access_key,
            "EDXAPP_AUTH_EXTRA": {
                "AWS_STORAGE_BUCKET_NAME": self.s3_bucket_name,
            },
            "EDXAPP_AWS_S3_CUSTOM_DOMAIN": "{}.s3.amazonaws.com".format(self.s3_bucket_name),
            "EDXAPP_IMPORT_EXPORT_BUCKET": self.s3_bucket_name,

            "XQUEUE_AWS_ACCESS_KEY_ID": self.s3_access_key,
            "XQUEUE_AWS_SECRET_ACCESS_KEY": self.s3_secret_access_key,
            "XQUEUE_UPLOAD_BUCKET": self.s3_bucket_name,
            "XQUEUE_UPLOAD_PATH_PREFIX": 'xqueue',

            "EDXAPP_GRADE_STORAGE_TYPE": 's3',
            "EDXAPP_GRADE_BUCKET": self.s3_bucket_name,
            "EDXAPP_GRADE_ROOT_PATH": 'grades-download',

            # Tracking logs
            "COMMON_OBJECT_STORE_LOG_SYNC": True,
            "COMMON_OBJECT_STORE_LOG_SYNC_BUCKET": self.s3_bucket_name,
            "COMMON_OBJECT_STORE_LOG_SYNC_PREFIX": 'logs/tracking/',
            "AWS_S3_LOGS": True,
            "AWS_S3_LOGS_ACCESS_KEY_ID": self.s3_access_key,
            "AWS_S3_LOGS_SECRET_KEY": self.s3_secret_access_key,
        }

    def _get_swift_settings(self):
        """
        Return dictionary of Swift Ansible settings.
        """
        return {
            "COMMON_ENABLE_OPENSTACK_INTEGRATION": True,
            "COMMON_EDXAPP_SETTINGS": "openstack",
            "EDXAPP_SETTINGS": "openstack",
            "XQUEUE_SETTINGS": "openstack_settings",

            "VHOST_NAME": "openstack",

            "EDXAPP_DEFAULT_FILE_STORAGE": "swift.storage.SwiftStorage",
            "EDXAPP_FILE_UPLOAD_STORAGE_BUCKET_NAME": self.swift_container_name,
            "EDXAPP_SWIFT_AUTH_VERSION": '2',
            "EDXAPP_SWIFT_USERNAME": self.swift_openstack_user,
            "EDXAPP_SWIFT_KEY": self.swift_openstack_password,
            "EDXAPP_SWIFT_TENANT_NAME": self.swift_openstack_tenant,
            "EDXAPP_SWIFT_AUTH_URL": self.swift_openstack_auth_url,
            "EDXAPP_SWIFT_REGION_NAME": self.swift_openstack_region,

            "EDXAPP_GRADE_STORAGE_CLASS": 'swift.storage.SwiftStorage',
            "EDXAPP_GRADE_STORAGE_KWARGS": {
                "name_prefix": 'grades-download/'
            },

            "XQUEUE_SWIFT_USERNAME": self.swift_openstack_user,
            "XQUEUE_SWIFT_KEY": self.swift_openstack_password,
            "XQUEUE_SWIFT_TENANT_NAME": self.swift_openstack_tenant,
            "XQUEUE_SWIFT_AUTH_URL": self.swift_openstack_auth_url,
            "XQUEUE_SWIFT_AUTH_VERSION": "{{ EDXAPP_SWIFT_AUTH_VERSION }}",
            "XQUEUE_SWIFT_REGION_NAME": self.swift_openstack_region,
            "XQUEUE_UPLOAD_BUCKET": self.swift_container_name,
            "XQUEUE_UPLOAD_PATH_PREFIX": 'xqueue',

            # Tracking logs
            "COMMON_OBJECT_STORE_LOG_SYNC": True,
            "COMMON_OBJECT_STORE_LOG_SYNC_BUCKET": self.swift_container_name,
            "COMMON_OBJECT_STORE_LOG_SYNC_PREFIX": "logs/tracking/",
            "SWIFT_LOG_SYNC_USERNAME": self.swift_openstack_user,
            "SWIFT_LOG_SYNC_PASSWORD": self.swift_openstack_password,
            "SWIFT_LOG_SYNC_TENANT_NAME": self.swift_openstack_tenant,
            "SWIFT_LOG_SYNC_AUTH_URL": self.swift_openstack_auth_url,
            "SWIFT_LOG_SYNC_REGION_NAME": self.swift_openstack_region,
        }

    def get_storage_settings(self):
        """
        Get configuration_storage_settings to pass to a new AppServer
        """
        if self.use_ephemeral_databases:
            # Workaround for broken CMS course export/import
            # caused by https://github.com/edx/edx-platform/pull/14552
            return yaml.dump({"EDXAPP_IMPORT_EXPORT_BUCKET": ""}, default_flow_style=False)

        if self.s3_access_key and self.s3_secret_access_key and self.s3_bucket_name:
            return yaml.dump(self._get_s3_settings(), default_flow_style=False)
        elif settings.SWIFT_ENABLE:
            # Only enable Swift if S3 isn't configured
            return yaml.dump(self._get_swift_settings(), default_flow_style=False)
        return ""
