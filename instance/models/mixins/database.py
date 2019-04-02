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
Instance app model mixins - Database
"""

# Imports #####################################################################

import functools
import inspect
import string
import warnings
import logging

from django.conf import settings
from django.db import models
from django.utils.crypto import get_random_string
import MySQLdb as mysql
from MySQLdb import Error as MySQLError
import pymongo
from pymongo.errors import PyMongoError

from instance.models.database_server import MySQLServer, MongoDBServer, MongoDBReplicaSet


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Functions ###################################################################

def database_name_escaped(func):
    """
    Decorator for functions that require name of MySQL database to be escaped.

    Escaping is necessary if a function uses the database name in a parameterized query;
    the driver doesn't escape it properly.
    """
    def wrapper(*args, **kwargs):
        """ Escape database name, then call func """
        signature = inspect.signature(func)
        bound_arguments = signature.bind(*args, **kwargs)
        # Obtain connection from cursor passed to func.
        # This allows us to simplify the signature of func (we don't have to add a "connection" parameter).
        connection = bound_arguments.arguments["cursor"].connection
        database = bound_arguments.arguments["database"]
        bound_arguments.arguments["database"] = connection.escape_string(database).decode()
        func(*bound_arguments.args, **bound_arguments.kwargs)
    return wrapper


def _get_mysql_cursor(mysql_server):
    """
    Get a database cursor.
    """
    try:
        connection = mysql.connect(
            host=mysql_server.hostname,
            user=mysql_server.username,
            passwd=mysql_server.password,
            port=mysql_server.port,
        )
    except MySQLError as exc:
        logger.exception('Cannot get MySQL cursor: %s. %s', mysql_server, exc)
        raise
    return connection.cursor()


@database_name_escaped
def _create_database(cursor, database):
    """
    Create MySQL database, if it doesn't already exist.
    """
    logger.info('Creating MySQL database: %s', database)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        cursor.execute('CREATE DATABASE IF NOT EXISTS `{db}` DEFAULT CHARACTER SET utf8'.format(db=database))


def _create_user(cursor, user, password):
    """
    Create MySQL user identified by password if it doesn't exist
    """
    # Newer versions of MySQL support "CREATE USER IF NOT EXISTS"
    # but at this point we can't be sure that all target hosts run one of these,
    # so we need to use a different approach for now:
    user_exists = cursor.execute("SELECT 1 FROM mysql.user WHERE user = %s", (user,))
    if not user_exists:
        logger.info('Creating mysql user: %s', user)
        cursor.execute('CREATE USER %s IDENTIFIED BY %s', (user, password,))


def _grant_privileges(cursor, database, user, privileges):
    """
    Grant privileges for databases to MySQL user
    """
    if database == "*":
        tables = "*.*"
    else:
        tables = "`{database}`.*".format(database=database)
    cursor.execute('GRANT {privileges} ON {tables} TO %s'.format(privileges=privileges, tables=tables), (user,))


@database_name_escaped
def _drop_database(cursor, database):
    """
    Drop MySQL database
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        logger.info('Dropping mysql db: %s', database)
        try:
            cursor.execute('DROP DATABASE IF EXISTS `{db}`'.format(db=database))
        except MySQLError as exc:
            logger.exception('Cannot drop MySQL database: %s. %s', database, exc)
            raise


def _drop_user(cursor, user):
    """
    Drop MySQL user if it exists
    """
    # Newer versions of MySQL support "DROP USER IF EXISTS"
    # but at this point we can't be sure that all target hosts run one of these,
    # so we need to use a different approach for now:
    user_exists = cursor.execute("SELECT 1 FROM mysql.user WHERE user = %s", (user,))
    if user_exists:
        logger.info('Dropping mysql user: %s.', user)
        try:
            cursor.execute('DROP USER %s', (user,))
        except MySQLError as exc:
            logger.exception('Cannot drop MySQL user: %s. %s', user, exc)
            raise


def select_random_mysql_server():
    """
    Helper for the field default of `mysql_server`.
    """
    return MySQLServer.objects.select_random().pk


def select_random_mongodb_server():
    """
    Helper for the field default of `mongodb_server`.
    """
    if getattr(settings, MongoDBServer.DEFAULT_SETTINGS_NAME, None):
        return MongoDBServer.objects.select_random().pk
    else:
        return None


def select_random_mongodb_replica_set():
    """
    Helper for the field default of `mongodb_server`.
    """
    if getattr(settings, MongoDBServer.DEFAULT_SETTINGS_NAME, None):
        return None
    else:
        return MongoDBReplicaSet.objects.select_random().pk


# Classes #####################################################################

class MySQLInstanceMixin(models.Model):
    """
    An instance that uses mysql databases
    """
    mysql_server = models.ForeignKey(
        MySQLServer,
        null=True,
        blank=True,
        default=select_random_mysql_server,
        on_delete=models.PROTECT,
    )

    mysql_user = models.CharField(
        max_length=16,  # 16 chars is mysql maximum
        # Note that the maximum length for the name of a MySQL user is 16 characters.
        # But since we add suffixes to mysql_user to generate unique user names
        # for different services (e.g. xqueue) we don't want to use the maximum length here.
        default=functools.partial(get_random_string, length=6, allowed_chars=string.ascii_lowercase),
        blank=True,
    )
    mysql_pass = models.CharField(
        max_length=32,
        blank=True,
        default=functools.partial(get_random_string, length=32),
    )
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
        if self.mysql_server:
            cursor = _get_mysql_cursor(self.mysql_server)

            # Create migration and read_only users
            _create_user(cursor, self.migrate_user, self._get_mysql_pass(self.migrate_user))
            _create_user(cursor, self.read_only_user, self._get_mysql_pass(self.read_only_user))

            # Create default databases and users, and grant privileges
            for database in self.mysql_databases:
                database_name = database["name"]
                _create_database(cursor, database_name)
                user = database["user"]
                _create_user(cursor, user, self._get_mysql_pass(user))
                privileges = database.get("priv", "ALL")
                _grant_privileges(cursor, database_name, user, privileges)
                _grant_privileges(cursor, database_name, self.migrate_user, "ALL")
                _grant_privileges(cursor, database_name, self.read_only_user, "ALL")
                additional_users = database.get("additional_users", [])
                for additional_user in additional_users:
                    _grant_privileges(cursor, database_name, additional_user["name"], additional_user["priv"])

            # Create admin user with appropriate privileges
            _create_user(cursor, self.admin_user, self._get_mysql_pass(self.admin_user))
            _grant_privileges(cursor, "*", self.admin_user, "CREATE USER")

            cursor.close()
            self.mysql_provisioned = True
            self.save()

    def deprovision_mysql(self, ignore_errors=False):
        """
        Drop all MySQL databases and users.
        """
        self.logger.info('Deprovisioning MySQL started.')
        if self.mysql_server and self.mysql_provisioned:
            try:
                cursor = _get_mysql_cursor(self.mysql_server)

                # Drop default databases and users
                for database in self.mysql_databases:
                    database_name = database["name"]
                    _drop_database(cursor, database_name)
                    _drop_user(cursor, database["user"])
                # Drop users with global privileges
                for user in self.global_users:
                    _drop_user(cursor, user)
            except MySQLError:
                if not ignore_errors:
                    raise

            self.mysql_provisioned = False
            self.save()
        self.logger.info('Deprovisioning MySQL finished.')


class MongoDBInstanceMixin(models.Model):
    """
    An instance that uses mongo databases
    """
    mongodb_server = models.ForeignKey(
        MongoDBServer,
        null=True,
        blank=True,
        default=select_random_mongodb_server,
        on_delete=models.PROTECT
    )

    mongodb_replica_set = models.ForeignKey(
        MongoDBReplicaSet,
        null=True,
        blank=True,
        default=select_random_mongodb_replica_set,
        on_delete=models.PROTECT
    )

    mongo_user = models.CharField(
        max_length=16,
        blank=True,
        default=functools.partial(get_random_string, length=16, allowed_chars=string.ascii_lowercase),
    )
    mongo_pass = models.CharField(
        max_length=32,
        blank=True,
        default=functools.partial(get_random_string, length=32),
    )
    mongo_provisioned = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def mongo_database_names(self):
        """
        An iterable of database names
        """
        return NotImplementedError

    @property
    def mongodb_servers(self):
        """
        Return all mongodb servers, or just the primary(s) if requested.

        If no replicaset configured, this is just the single mongodb server.
        """
        if self.mongodb_replica_set:
            mongodb_servers = MongoDBServer.objects.filter(
                replica_set=self.mongodb_replica_set,
            )
        else:
            mongodb_servers = [self.mongodb_server]
        return mongodb_servers

    @property
    def primary_mongodb_server(self):
        """
        Returns the primary (or single) mongodb server.
        """
        mongodb_servers = self.mongodb_servers
        if self.mongodb_replica_set:
            mongodb_servers = mongodb_servers.filter(primary=True)
        return mongodb_servers[0]

    def _get_main_database_url(self):
        """
        Returns main database url from replica set, or url from single server
        """
        try:
            return self.primary_mongodb_server.url
        except AttributeError:
            return None

    def provision_mongo(self):
        """
        Create mongo user and databases
        """
        database_url = self._get_main_database_url()
        if database_url:
            mongo = pymongo.MongoClient(database_url)
            for database in self.mongo_database_names:
                # May update the password if the user already exists
                self.logger.info('Creating mongo db: %s', database)
                mongo[database].add_user(self.mongo_user, self.mongo_pass)
            self.mongo_provisioned = True
            self.save()

    def deprovision_mongo(self, ignore_errors=False):
        """
        Drop Mongo databases.
        """
        self.logger.info('Deprovisioning Mongo started.')
        database_url = self._get_main_database_url()
        if database_url and self.mongo_provisioned:
            mongo = pymongo.MongoClient(database_url)
            for database in self.mongo_database_names:
                # Dropping a non-existing database is a no-op.  Users are dropped together with the DB.
                self.logger.info('Dropping mongo db: %s.', database)
                try:
                    mongo.drop_database(database)
                except PyMongoError as exc:
                    self.logger.exception('Cannot drop Mongo database: %s. %s', database, exc)
                    if not ignore_errors:
                        raise
            self.mongo_provisioned = False
            self.save()
        self.logger.info('Deprovisioning Mongo finished.')
