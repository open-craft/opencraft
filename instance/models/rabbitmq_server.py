# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <xavier@opencraft.com>
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
Instance app models - RabbitMQ Server model and manager
"""

# Imports #####################################################################

import logging
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django_extensions.db.models import TimeStampedModel

from instance.models.shared_server import SharedServerManager
from .utils import ValidateModelMixin


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Constants ###################################################################

DEFAULT_INSTANCE_RABBITMQ_PORT = 5671


# Models ######################################################################

class RabbitMQServerManager(SharedServerManager):
    """
    Custom manager for the RabbitMQServer model.
    """

    def _create_default(self):
        """
        Create the default RabbitMQ server configured in the Django settings, if any.
        """
        if settings.DEFAULT_RABBITMQ_API_URL:
            api_url = urlparse(settings.DEFAULT_RABBITMQ_API_URL)
            amqps_url = urlparse(settings.DEFAULT_INSTANCE_RABBITMQ_URL)
            # Construct the part of the URL containing basic auth in order to rip it out of the URL
            api_credentials = '{}:{}@'.format(api_url.username or '', api_url.password or '')
            api_url_without_credentials = api_url.geturl().replace(api_credentials, '')

            defaults = {
                'api_url': api_url_without_credentials,
                'admin_username': api_url.username,
                'admin_password': api_url.password,
                'instance_host': amqps_url.hostname,
                'instance_port': amqps_url.port,
                'accepts_new_clients': True,
            }

            if not all(defaults.values()):
                raise ImproperlyConfigured(
                    "Found DEFAULT_RABBITMQ_API_URL, but it must contain basic auth credentials, and "
                    "DEFAULT_INSTANCE_RABBITMQ_URL must contain both a hostname and port"
                )
            logger.info("Creating RabbitMQServer %s", defaults['instance_host'])

            passed_defaults = defaults.copy()
            del passed_defaults['api_url']
            passed_defaults['name'] = passed_defaults['instance_host']
            server, created = self.get_or_create(
                api_url=api_url_without_credentials,
                defaults=passed_defaults,
            )
            if not created and not all(getattr(server, name) == default for name, default in defaults.items()):
                logger.warning(
                    "RabbitMQServer for %s already exists, and its settings do not match "
                    "the Django settings: " + ", ".join(["%s vs %s"] * len(defaults)),
                    *sum(sorted(defaults.items()), ()),
                )


class RabbitMQServer(ValidateModelMixin, TimeStampedModel):
    """
    A model representing a configured RabbitMQ server.
    """
    objects = RabbitMQServerManager()

    class Meta:
        verbose_name = 'RabbitMQ Server'

    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=250, blank=True)

    # URL and credentials for accessing this API of the RabbitMQ server.
    # User identified by these credentials must have permission to manage all
    # vhosts, users, and roles.
    api_url = models.URLField(max_length=200, unique=True)
    admin_username = models.CharField(max_length=64)
    admin_password = models.CharField(max_length=128)

    # Host name or IP address of this database server
    instance_host = models.CharField(max_length=128)

    # Port to use when accessing this database server
    instance_port = models.PositiveIntegerField(default=DEFAULT_INSTANCE_RABBITMQ_PORT)

    # Does this database server currently accept new clients (i.e., instances)?
    accepts_new_clients = models.BooleanField(default=False)

    def __str__(self):
        description = ''
        if self.description:
            description = ' ({description})'.format(description=self.description)
        return '{name}{description}'.format(
            name=self.name,
            description=description
        )
