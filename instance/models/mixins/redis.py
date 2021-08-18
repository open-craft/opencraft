# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <contact@opencraft.com>
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
Instance app model mixins - Redis
"""

# Imports #####################################################################

from functools import lru_cache
import redis
import json
import string
import urllib.parse

from django.db import IntegrityError, models
from django.utils.crypto import get_random_string
import requests

from instance.models.redis_server import RedisServer


# Functions ###################################################################

def random_username():
    return get_random_string(32, allowed_chars=string.ascii_lowercase)

def random_password():
    return get_random_string(64)

def select_random_redis_server():
    """
    Helper for the field default of `redis_server`.

    The random server selection does not make sense in case if one RedisServer
    is available at a time, though if multiple servers are registered it serves
    as a very basic "load balancer".

    It selects a random server that accepts new connections. If the default
    Redis instance's URL is set, it also creates a Redis server based on it.
    """
    return RedisServer.objects.select_random().pk


# Classes #####################################################################

class RedisAPIError(Exception):
    """Exception indicating that a call to the Redis API failed."""


class RedisInstanceMixin(models.Model):
    """
    An instance that uses a Redis db with a set of users.
    """

    redis_server = models.ForeignKey(
        RedisServer,
        null=True,
        blank=True,
        default=select_random_redis_server,
        on_delete=models.PROTECT,
    )

    redis_username = models.CharField(max_length=32, default=random_username, unique=True)
    redis_password = models.CharField(max_length=64, default=random_password)
    redis_provisioned = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @lru_cache()
    def _redis_client(self, **kwargs):
        """
        Generic method for sending an HTTP request to the Redis API.
        Raises a RedisAPIError if the response isn't OK.
        """

        return redis.Redis(
            username=self.redis_server.admin_username,
            password=self.redis_server.admin_password,
            host=self.redis_server.instance_host,
            port=self.redis_server.instance_port,
            db=self.redis_server.instance_db,
            ssl=self.redis_server.use_ssl_connections,
            **kwargs
        )

    @property
    def redis_key_prefix(self) -> str:
        """
        Return the key prefix for the user.

        Username used to prefix redis keys and set ACLs on the Redis server.
        """
        return f"{self.redis_username}_"

    def delete_redis_acl(self, client: redis.Redis):
        """
        Delete ACL record for user.
        """
        client.acl_deluser(self.redis_username)

    def create_redis_acl(self, client: redis.Redis):
        """
        Create ACL record for user.
        """
        client.acl_setuser(
            username=self.redis_username,
            passwords=[f"+{self.redis_password}"],
            keys=[self.redis_key_prefix],
            enabled=True
        )

    def provision_redis(self):
        """
        Creates the Redis users.
        """
        if self.redis_provisioned:
            self.logger.info(
                'Redis is already provisioned for %s. No provisioning needed.',
                self.redis_username
            )

            return

        self.logger.info('Provisioning Redis started.')

        client = self._redis_client()
        self.create_redis_acl(client)

        self.redis_provisioned = True
        self.save()

    def deprovision_redis(self, ignore_errors=False):
        """
        Deletes the Redis vhost and users.
        """
        if not self.redis_provisioned:
            self.logger.info(
                'Redis is not provisioned for %s. No deprovisioning needed.',
                self.redis_username
            )

            return

        self.logger.info('Deprovisioning Redis started.')
        self.logger.info('Deleting redis user: %s', self.redis_username)

        try:
            client = self._redis_client()
            self.delete_redis_acl(client)
        except Exception as exc:
            self.logger.exception(
                'Cannot delete redis user: %s. %s',
                self.redis_username,
                exc
            )

            if not ignore_errors:
                raise exc

        self.redis_provisioned = False
        self.save()

        self.logger.info('Deprovisioning Redis finished.')
