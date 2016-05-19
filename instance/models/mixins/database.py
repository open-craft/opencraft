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
Instance app model mixins - Database
"""

# Imports #####################################################################

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string
import MySQLdb as mysql
import pymongo


# Functions ###################################################################

def _get_mysql_cursor():
    """
    Get a database cursor.
    """
    connection = mysql.connect(
        host=settings.INSTANCE_MYSQL_URL_OBJ.hostname,
        user=settings.INSTANCE_MYSQL_URL_OBJ.username,
        passwd=settings.INSTANCE_MYSQL_URL_OBJ.password or '',
        port=settings.INSTANCE_MYSQL_URL_OBJ.port or 3306,
    )
    return connection.cursor(), connection


def _create_database(cursor, database):
    """
    Create MySQL database
    """
    cursor.execute('CREATE DATABASE `{0}` DEFAULT CHARACTER SET utf8'.format(database))


def _create_user(cursor, user, password):
    """
    Create MySQL user identified by password
    """
    cursor.execute('CREATE USER %s IDENTIFIED BY %s', (user, password,))


def _grant_privileges(cursor, database, user, privileges):
    """
    Grant privileges for databases to MySQL user
    """
    if database == "*":
        tables = "*.*"
    else:
        tables = "`{0}`.*".format(database)
    cursor.execute('GRANT %s ON {0} TO %s'.format(tables), (privileges, user,))


def _drop_database(cursor, database):
    """
    Drop MySQL database
    """
    cursor.execute('DROP DATABASE IF EXISTS `{0}`'.format(database))


def _drop_user(cursor, user):
    """
    Drop MySQL user
    """
    cursor.execute('DROP USER %s', (user,))


# Classes #####################################################################

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
    def mysql_databases(self):
        """
        An iterable of databases
        """
        return NotImplementedError

    def provision_mysql(self):
        """
        Create mysql user and databases
        """
        if settings.INSTANCE_MYSQL_URL_OBJ and not self.mysql_provisioned:
            cursor, connection = _get_mysql_cursor()

            # Create migration user
            _create_user(cursor, self.migrate_user, get_random_string(length=32))

            # Create default databases and users, and grant privileges
            for database in self.mysql_databases:
                # We can't use the database name in a parameterized query, the
                # driver doesn't escape it properly. So we escape it here instead
                database_name = connection.escape_string(database["name"]).decode()
                _create_database(cursor, database_name)
                user = database["user"]
                _create_user(cursor, user, get_random_string(length=32))
                privileges = database.get("priv", "ALL")
                _grant_privileges(cursor, database_name, user, privileges)
                _grant_privileges(cursor, database_name, self.migrate_user, "ALL")
                additional_users = database.get("additional_users", [])
                for additional_user in additional_users:
                    _grant_privileges(cursor, database_name, additional_user["name"], additional_user["priv"])

            # Create read_only user with appropriate privileges
            _create_user(cursor, self.read_only_user, get_random_string(length=32))
            _grant_privileges(cursor, "*", self.read_only_user, "ALL")

            # Create admin user with appropriate privileges
            _create_user(cursor, self.admin_user, get_random_string(length=32))
            _grant_privileges(cursor, "*", self.admin_user, "CREATE USER")

            self.mysql_provisioned = True
            self.save()

    def deprovision_mysql(self):
        """
        Drop all MySQL databases and users.
        """
        if settings.INSTANCE_MYSQL_URL_OBJ and self.mysql_provisioned:
            cursor, connection = _get_mysql_cursor()

            # Drop default databases and users
            for database in self.mysql_databases:
                # We can't use the database name in a parameterized query, the
                # driver doesn't escape it properly. So we escape it here instead
                database_name = connection.escape_string(database["name"]).decode()
                _drop_database(cursor, database_name)
                _drop_user(cursor, database["user"])

            # Drop users with global privileges
            for user in self.global_users:
                _drop_user(cursor, user)

            self.mysql_provisioned = False
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
    def mongo_database_names(self):
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

    def deprovision_mongo(self):
        """
        Drop Mongo databases.
        """
        if settings.INSTANCE_MONGO_URL and self.mongo_provisioned:
            mongo = pymongo.MongoClient(settings.INSTANCE_MONGO_URL)
            for database in self.mongo_database_names:
                # Dropping a non-existing database is a no-op.  Users are dropped together with the DB.
                mongo.drop_database(database)
            self.mongo_provisioned = False
            self.save()
