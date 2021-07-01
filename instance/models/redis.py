# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <xavier@opencraft.com>
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
Definition of Redis-specific models.
"""
import redis
from django.db import models
from django_extensions.db.models import TimeStampedModel

from instance.models.utils import ValidateModelMixin


class RedisUser(ValidateModelMixin, TimeStampedModel):
    """
    A model representing a single Redis user identified by ACLs.
    """

    # TODO: The user can have multiple passwords set by ACLs. Create signals to
    # handle ACL setting on user creation, ACL update on password change, and
    # ACL deletion on user deletion.

    # Username of the user will be used to prefix redis keys and set ACLs on
    # the server for the user.
    username = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=64)

    def __str__(self):
        return self.username

    @property
    def key_prefix(self) -> str:
        """
        Return the key prefix for the user.

        Username used to prefix redis keys and set ACLs on the Redis server.
        """
        return f"{self.username}_"

    def delete_acl(self, client: redis.Redis):
        """
        Delete ACL record for user.
        """
        client.acl_deluser(self.username)

    def create_acl(self, client: redis.Redis):
        """
        Create ACL record for user.
        """
        client.acl_setuser(
            username=self.username,
            passwords=[f"+{self.password}"],
            keys=[self.key_prefix],
            enabled=True
        )
