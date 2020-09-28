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
OpenCraft views
"""

# Imports #####################################################################

from consul import Consul
from django.db import connection
from django.http import HttpResponse
from django.views.generic.base import RedirectView
from django.views.generic import View
from django.urls import reverse
from django.conf import settings
from huey.contrib.djhuey import HUEY
from psycopg2 import OperationalError
from redis.exceptions import ConnectionError as RedisConnectionError
from requests.exceptions import ConnectionError as RequestsConnectionError

from instance.models.instance import InstanceReference

# Views #######################################################################


class IndexView(RedirectView):
    """
    Index view
    """
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        """
        Redirect instance manager users to the instance list, and anyone else to the registration form
        """
        user = self.request.user
        if InstanceReference.can_manage(user):
            return reverse('instance:index')
        elif user.is_authenticated is False:
            return reverse('login')
        else:
            return settings.USER_CONSOLE_FRONTEND_URL


class HealthCheckView(View):
    """
    Health Check view
    """
    def get(self, request):
        """
        GET method which returns 503 status if any required services are unreachable.
        """
        try:
            # Verify that the postgres database backend is reachable
            #
            # Note that at the time of writing this, this view will not even get loaded if postgres is down due to an
            # exception being thrown in instance.logging.DBHandler.emit which gets called before the view.
            # This check exists so that we can monitor postgres even if the logging behaviour changes in the future.
            self._check_postgres_connection()
        except OperationalError:
            return HttpResponse('Postgres unreachable', status=503)

        try:
            # Verify that the huey redis database backend is reachable
            self._check_redis_connection()
        except RedisConnectionError:
            return HttpResponse('Redis unreachable', status=503)

        try:
            # Verify that the consul agent is reachable
            self._check_consul_connection()
        except RequestsConnectionError:
            return HttpResponse('Consul unreachable', status=503)

        return HttpResponse()

    def _check_postgres_connection(self):
        """
        Attempts establishing a connection with postgres to check connection
        """
        connection.connect()

    def _check_redis_connection(self):
        """
        Runs the redis ECHO command to check connection
        """
        HUEY.get_storage().conn.echo('health_check')

    def _check_consul_connection(self):
        """
        Returns the services registered with Consul to check connection
        """
        Consul().agent.services()
