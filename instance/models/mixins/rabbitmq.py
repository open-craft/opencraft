# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
import string
import urllib.parse

from django.db import IntegrityError, models
from django.utils.crypto import get_random_string
import requests

from instance.models.rabbitmq import RabbitMQUser
from instance.models.rabbitmq_server import RabbitMQServer


# Functions ###################################################################

def generate_random_vhost():
    """
    Helper function for the default value of the field `rabbitmq_vhost`.
    """
    return '/{id}'.format(
        id=get_random_string(length=14, allowed_chars=string.ascii_lowercase)
    )


def new_rabbitmq_user():
    """
    Return the primary key of a new RabbitMQ user.
    """
    for _ in range(200):
        # Keep retrying until we get a unique username.
        try:
            return RabbitMQUser.objects.create(
                username=get_random_string(length=32, allowed_chars=string.ascii_lowercase),
                password=get_random_string(length=64)
            ).pk
        except IntegrityError:
            pass

    raise IntegrityError


def select_random_rabbitmq_server():
    """
    Helper for the field default of `rabbitmq_server`.
    """
    return RabbitMQServer.objects.select_random().pk


# Classes #####################################################################

class RabbitMQAPIError(Exception):
    """Exception indicating that a call to the RabbitMQ API failed."""


class RabbitMQInstanceMixin(models.Model):
    """
    An instance that uses a RabbitMQ vhost with a set of users.
    """
    rabbitmq_server = models.ForeignKey(
        RabbitMQServer,
        null=True,
        blank=True,
        default=select_random_rabbitmq_server,
        on_delete=models.PROTECT,
    )

    rabbitmq_vhost = models.CharField(max_length=16, blank=True, default=generate_random_vhost)
    rabbitmq_provider_user = models.ForeignKey(
        RabbitMQUser,
        related_name='provider_instance',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=new_rabbitmq_user,
    )
    rabbitmq_consumer_user = models.ForeignKey(
        RabbitMQUser,
        related_name='consumer_instance',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        default=new_rabbitmq_user,
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

        url = '{api_url}/api/{args}'.format(api_url=self.rabbitmq_server.api_url, args=formatted_args)
        response = getattr(requests, action)(
            url,
            auth=(self.rabbitmq_server.admin_username, self.rabbitmq_server.admin_password),
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
