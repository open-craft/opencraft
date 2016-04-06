# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
Instance app model mixins - Database
"""
import MySQLdb as mysql
import pymongo
from django.conf import settings
from django.db import models


class MySQLInstanceMixin(models.Model):
    """
    An instance that uses mysql databases
    """
    mysql_user = models.CharField(max_length=16, blank=True)  # 16 chars is mysql maximum
    mysql_pass = models.CharField(max_length=32, blank=True)
    mysql_provisioned = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def mysql_database_names(self):  # pylint: disable=no-self-use
        """
        An iterable of database names
        """
        return NotImplementedError

    def provision_mysql(self):
        """
        Create mysql user and databases
        """
        if settings.INSTANCE_MYSQL_URL_OBJ and not self.mysql_provisioned:
            connection = mysql.connect(
                host=settings.INSTANCE_MYSQL_URL_OBJ.hostname,
                user=settings.INSTANCE_MYSQL_URL_OBJ.username,
                passwd=settings.INSTANCE_MYSQL_URL_OBJ.password or '',
                port=settings.INSTANCE_MYSQL_URL_OBJ.port or 3306,
            )
            cursor = connection.cursor()

            for database in self.mysql_database_names:
                # We can't use the database name in a parameterized query, the
                # driver doesn't escape it properly. Se we escape it here instead
                database_name = connection.escape_string(database).decode()
                cursor.execute('CREATE DATABASE `{0}` DEFAULT CHARACTER SET utf8'.format(database_name))
                cursor.execute('GRANT ALL ON `{0}`.* TO %s IDENTIFIED BY %s'.format(database_name),
                               (self.mysql_user, self.mysql_pass))

            self.mysql_provisioned = True
            self.save()


class MongoDBInstanceMixin(models.Model):
    """
    An instance that uses mongo databases
    """
    mongo_user = models.CharField(max_length=16, blank=True)
    mongo_pass = models.CharField(max_length=32, blank=True)
    mongo_provisioned = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def mongo_database_names(self): # pylint: disable=no-self-use
        """
        An iterable of database names
        """
        return NotImplementedError

    def provision_mongo(self):
        """
        Create mongo user and databases
        """
        if settings.INSTANCE_MONGO_URL and not self.mongo_provisioned:
            mongo = pymongo.MongoClient(settings.INSTANCE_MONGO_URL)
            for database in self.mongo_database_names:
                mongo[database].add_user(self.mongo_user, self.mongo_pass)

            self.mongo_provisioned = True
            self.save()
