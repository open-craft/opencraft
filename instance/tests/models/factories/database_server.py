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
Factories for DatabaseServer models.
"""

# Imports #####################################################################

import factory
from factory.django import DjangoModelFactory

from instance.models.database_server import MySQLServer, MongoDBServer


# Classes #####################################################################

class MySQLServerFactory(DjangoModelFactory):
    """
    Factory for the MySQLServer model.
    """
    class Meta:
        model = MySQLServer

    name = factory.Sequence('mysql-server-{}'.format)
    hostname = factory.Sequence('mysql-server-{}'.format)


class MongoDBServerFactory(DjangoModelFactory):
    """
    Factory for the MongoDBServer model.
    """
    class Meta:
        model = MongoDBServer

    name = factory.Sequence('mysql-server-{}'.format)
    hostname = factory.Sequence('mongodb-server-{}'.format)
