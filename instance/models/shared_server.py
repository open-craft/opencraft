# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
Instance app models - Database Server models
"""

# Imports #####################################################################

import logging
import random

from django.db import models, transaction


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Models ######################################################################

class SharedServerManager(models.Manager):
    """
    Abstract class for custom server model managers.
    """

    class Meta:
        abstract = True

    def _create_default(self):
        """
        Base class should create at least one default server record.
        """
        raise NotImplementedError

    def filter_accepts_new_clients(self):
        """
        Returns a query selector of servers accepting new clients.
        """
        return self.filter(accepts_new_clients=True)

    def select_random(self):
        """
        Select a server for a new instance.
        The current implementation selects one of the servers that accept new clients at random.
        If no database server accepts new clients, DoesNotExist is raised.
        """
        self._create_default()

        # The set of servers might change between retrieving the server count and retrieving the random server,
        # so we make this atomic.
        with transaction.atomic():
            servers = self.filter_accepts_new_clients()
            count = servers.count()
            if not count:
                raise self.model.DoesNotExist(
                    "No configured {} accepts new clients.".format(self.__class__.__name__)
                )
            return servers[random.randrange(count)]
