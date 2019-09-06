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
Media storage classes
"""

from django.conf import settings
from storages.backends.s3bot3 import S3Boto3Storage


class S3MediaStorage(S3Boto3Storage):
    """
    A custom media storage backend for django-storages extending the S3Boto3Storage backend.
    """
    access_key = settings.MEDIAFILES_AWS_S3_ACCESS_KEY_ID
    secret_key = settings.MEDIAFILES_AWS_S3_SECRET_ACCESS_KEY
    bucket_name = settings.MEDIAFILES_AWS_S3_BUCKET_NAME
    region_name = settings.MEDIAFILES_AWS_S3_REGION_NAME
    signature_version = settings.MEDIAFILES_AWS_S3_SIGNATURE_VERSION
    querystring_expire = settings.MEDIAFILES_AWS_S3_QUERYSTRING_EXPIRE
    default_acl = 'private'
