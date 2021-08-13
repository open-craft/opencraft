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
Instance app models - Redis Server model and manager
"""

# Imports #####################################################################

import logging
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django_extensions.db.models import TimeStampedModel

from instance.models.shared_server import SharedServerManager
from instance.models.utils import ValidateModelMixin


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Constants ###################################################################

DEFAULT_INSTANCE_REDIS_PORT = 5671
DEFAULT_INSTANCE_REDIS_DB = 0


# Models ######################################################################

class RedisServerManager(SharedServerManager):
    """
    Custom manager for the RedisServer model.
    """

    def _create_default(self):
        """
        Create the default Redis server configured in the Django settings, if any.
        """
        if settings.DEFAULT_INSTANCE_REDIS_URL:
            conn_params = urlparse(settings.DEFAULT_INSTANCE_REDIS_URL)

            defaults = {
                'admin_username': conn_params.username,
                'admin_password': conn_params.password,
                'instance_host': conn_params.hostname,
                'instance_port': conn_params.port,
                'instance_db': conn_params.path.replace("/", ""),
                'accepts_new_clients': True,
            }

            if not all(defaults.values()):
                raise ImproperlyConfigured(
                    "Found DEFAULT_INSTANCE_REDIS_URL, but it must contain "
                    "basic auth credentials, hostname, port and db."
                )

            logger.info("Creating RedisServer %s", defaults['instance_host'])

            defaults['name'] = defaults['instance_host']
            defaults['instance_db'] = int(defaults['instance_db'])
            defaults['use_ssl_connections'] = conn_params.scheme == "rediss"

            server, created = self.get_or_create(defaults=defaults)

            if not created and not all(getattr(server, name) == default for name, default in defaults.items()):
                logger.warning(
                    "RedisServer for %s already exists, and its settings do not match "
                    "the Django settings: " + ", ".join(["%s vs %s"] * len(defaults)),
                    *sum(sorted(defaults.items()), ()),
                )


class RedisServer(ValidateModelMixin, TimeStampedModel):
    """
    A model representing a configured Redis server.
    """
    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=250, blank=True)

    # Credentials for accessing the Redis server.
    # User identified by these credentials must have permission to manage ACLs.
    admin_username = models.CharField(max_length=64)
    admin_password = models.CharField(max_length=128)

    instance_host = models.CharField(max_length=128)
    instance_port = models.PositiveIntegerField(default=DEFAULT_INSTANCE_REDIS_PORT)
    instance_db = models.PositiveIntegerField(default=DEFAULT_INSTANCE_REDIS_DB)

    use_ssl_connections = models.BooleanField(default=True)
    accepts_new_clients = models.BooleanField(default=False)

    objects = RedisServerManager()


    class Meta:
        verbose_name = 'Redis Server'

    def __str__(self) -> str:
        description = f' ({self.description})' if self.description else ''
        return f'{self.name}{description}'
