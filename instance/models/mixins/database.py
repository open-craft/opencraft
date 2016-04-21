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

from django.conf import settings
from django.db import models
import MySQLdb as mysql
import pymongo
from swiftclient.exceptions import ClientException as SwiftClientException

from instance import openstack


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
            cursor, connection = _get_mysql_cursor()
            for database in self.mysql_database_names:
                # We can't use the database name in a parameterized query, the
                # driver doesn't escape it properly. Se we escape it here instead
                database_name = connection.escape_string(database).decode()
                cursor.execute('CREATE DATABASE `{0}` DEFAULT CHARACTER SET utf8'.format(database_name))
                cursor.execute('GRANT ALL ON `{0}`.* TO %s IDENTIFIED BY %s'.format(database_name),
                               (self.mysql_user, self.mysql_pass))
            self.mysql_provisioned = True
            self.save()

    def deprovision_mysql(self):
        """
        Drop all MySQL databases.
        """
        if settings.INSTANCE_MYSQL_URL_OBJ and self.mysql_provisioned:
            cursor, connection = _get_mysql_cursor()
            for database in self.mysql_database_names:
                # We can't use the database name in a parameterized query, the
                # driver doesn't escape it properly. Se we escape it here instead
                database_name = connection.escape_string(database).decode()
                cursor.execute('DROP DATABASE IF EXISTS `{0}`'.format(database_name))
            cursor.execute('DROP USER %s', (self.mysql_user,))
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


class SwiftContainerInstanceMixin(models.Model):
    """
    Mixin to provision Swift containers for an instance.
    """
    swift_openstack_user = models.CharField(max_length=32, blank=True)
    swift_openstack_password = models.CharField(max_length=64, blank=True)
    swift_openstack_tenant = models.CharField(max_length=32, blank=True)
    swift_openstack_auth_url = models.URLField(blank=True)
    swift_openstack_region = models.CharField(max_length=16, blank=True)
    swift_provisioned = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def swift_container_names(self):  # pylint: disable=no-self-use
        """
        An iterable of Swift container names.
        """
        return NotImplementedError

    def provision_swift(self):
        """
        Create the Swift containers if necessary.
        """
        if settings.SWIFT_ENABLE and not self.swift_provisioned:
            for container_name in self.swift_container_names:
                openstack.create_swift_container(
                    container_name,
                    user=self.swift_openstack_user,
                    password=self.swift_openstack_password,
                    tenant=self.swift_openstack_tenant,
                    auth_url=self.swift_openstack_auth_url,
                    region=self.swift_openstack_region,
                )
            self.swift_provisioned = True
            self.save()

    def deprovision_swift(self):
        """
        Delete the Swift containers.
        """
        if settings.SWIFT_ENABLE and self.swift_provisioned:
            for container_name in self.swift_container_names:
                try:
                    openstack.delete_swift_container(
                        container_name,
                        user=self.swift_openstack_user,
                        password=self.swift_openstack_password,
                        tenant=self.swift_openstack_tenant,
                        auth_url=self.swift_openstack_auth_url,
                        region=self.swift_openstack_region,
                    )
                except SwiftClientException:
                    # If deleting a Swift container fails, we still want to continue.
                    self.logger.exception(
                        'Could not delete Swift container "%s".', container_name, exc_info=True
                    )
            self.swift_provisioned = False
            self.save()
