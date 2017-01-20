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
Instance app model mixins - RabbitMQ
"""

# Imports #####################################################################

import json
import requests
import urllib.parse

from django.conf import settings
from django.db import models

from instance.models.rabbitmq import RabbitMQUser


# Classes #####################################################################

class RabbitMQAPIError(Exception):
    """Exception indicating that a call to the RabbitMQ API failed."""


class RabbitMQInstanceMixin(models.Model):
    """
    An instance that uses a RabbitMQ vhost with a set of users.
    """
    rabbitmq_vhost = models.CharField(max_length=16, blank=True)
    rabbitmq_provider_user = models.ForeignKey(
        RabbitMQUser,
        related_name='provider_instance',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    rabbitmq_consumer_user = models.ForeignKey(
        RabbitMQUser,
        related_name='consumer_instance',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    rabbitmq_provisioned = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def _rabbitmq_request(self, action, *url_args, data=None):
        """
        Generic method for sending an HTTP request to the RabbitMQ API.
        Raises a RabbitMQAPIError if the response isn't OK.
        """
        formatted_args = '/'.join(urllib.parse.quote(arg, safe='') for arg in url_args)
        if data is not None:
            data = json.dumps(data)

        url = '{api_url}/api/{args}'.format(api_url=settings.RABBITMQ_API_URL, args=formatted_args)
        response = getattr(requests, action)(
            url,
            auth=(settings.RABBITMQ_ADMIN_USERNAME, settings.RABBITMQ_ADMIN_PASSWORD),
            headers={'content-type': 'application/json'},
            data=data
        )

        if not response.ok:
            self.logger.error(
                "RabbitMQ API call failed for instance %s. URL: %s. Verb: %s. Response status: %s.",
                self,
                url,
                action,
                response.status_code
            )
            raise RabbitMQAPIError
        return response

    def provision_rabbitmq(self):
        """
        Creates the RabbitMQ vhost and users.
        """
        if not self.rabbitmq_provisioned:
            self._rabbitmq_request('put', 'vhosts', self.rabbitmq_vhost)

            for user in [self.rabbitmq_provider_user, self.rabbitmq_consumer_user]:
                self._rabbitmq_request('put', 'users', user.username, data={
                    'password': user.password,
                    'tags': user.username,
                })
                self._rabbitmq_request('put', 'permissions', self.rabbitmq_vhost, user.username, data={
                    'configure': '.*',
                    'write': '.*',
                    'read': '.*'
                })
        self.rabbitmq_provisioned = True
        self.save()

    def deprovision_rabbitmq(self):
        """
        Deletes the RabbitMQ vhost and users.
        """
        if self.rabbitmq_provisioned:
            self._rabbitmq_request('delete', 'vhosts', self.rabbitmq_vhost)
            for user in [self.rabbitmq_consumer_user, self.rabbitmq_provider_user]:
                self._rabbitmq_request('delete', 'users', user.username)
        self.rabbitmq_provisioned = False
        self.save()
