# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <xavier@opencraft.com>
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
Open edX instance database mixin
"""
import string
import uuid

from django.conf import settings
from django.template import loader
from django.utils.crypto import get_random_string

from .database import MySQLInstanceMixin, MongoDBInstanceMixin


# Classes #####################################################################

class OpenEdXDatabaseMixin(MySQLInstanceMixin, MongoDBInstanceMixin):
    """
    Mixin that provides functionality required for the database backends that an
    OpenEdX Instance uses (when not using ephemeral databases)

    TODO: ElasticSearch?
    """
    class Meta:
        abstract = True

    @property
    def mysql_database_name(self):
        """
        The mysql database name for this instance
        """
        return self.database_name

    @property
    def mysql_databases(self):
        """
        List of mysql databases
        """
        return [
            {
                "name": self._get_mysql_database_name("ecommerce"),
                "user": self._get_mysql_user_name("ecomm001"),
            },
            {
                "name": self._get_mysql_database_name("dashboard"),
                "user": self._get_mysql_user_name("rosencrantz"),
            },
            {
                "name": self._get_mysql_database_name("xqueue"),
                "user": self._get_mysql_user_name("xqueue001"),
            },
            {
                "name": self._get_mysql_database_name("edxapp"),
                "user": self._get_mysql_user_name("edxapp001"),
            },
            {
                "name": self._get_mysql_database_name("edxapp_csmh"),
                "user": self._get_mysql_user_name("edxapp_csmh001"),
            },
            {
                "name": self._get_mysql_database_name("edx_notes_api"),
                "user": self._get_mysql_user_name("notes001"),
                "priv": "SELECT,INSERT,UPDATE,DELETE",
            },
            {
                "name": self._get_mysql_database_name("analytics-api"),
                "user": self._get_mysql_user_name("api001"),
            },
            {
                "name": self._get_mysql_database_name("reports"),
                "user": self._get_mysql_user_name("reports001"),
                "priv": "SELECT",
                "additional_users": [
                    {
                        "name": self._get_mysql_user_name("api001"),
                        "priv": "SELECT",
                    }
                ],
            },
        ]

    @property
    def mongo_database_name(self):
        """
        The name of the main external mongo database
        """
        return self.database_name

    @property
    def forum_database_name(self):
        """
        The name of the external database used for forums
        """
        return '{0}_forum'.format(self.database_name)

    @property
    def mongo_database_names(self):
        """
        List of mongo database names
        """
        return [self.mongo_database_name, self.forum_database_name]

    @property
    def migrate_user(self):
        """
        Name of migration user
        """
        return self._get_mysql_user_name("migrate")

    @property
    def read_only_user(self):
        """
        Name of read_only user
        """
        return self._get_mysql_user_name("read_only")

    @property
    def admin_user(self):
        """
        Name of admin user
        """
        return self._get_mysql_user_name("admin")

    @property
    def global_users(self):
        """
        List of MySQL users with global privileges (i.e., privileges spanning multiple databases)
        """
        return self.migrate_user, self.read_only_user, self.admin_user

    def _get_mysql_database_name(self, suffix):
        """
        Build unique name for MySQL database using suffix
        """
        return "{0}_{1}".format(self.mysql_database_name, suffix)

    def _get_mysql_user_name(self, suffix):
        """
        Build unique name for MySQL user using suffix
        """
        return "{0}_{1}".format(self.mysql_user, suffix)

    def _get_mysql_pass(self, user):
        """
        Build unique password for user, derived from MySQL password for this instance and user
        """
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, self.mysql_pass + user))

    def set_field_defaults(self):
        """
        Set default values for mysql and mongo credentials.

        Don't change existing values on subsequent calls.

        Credentials are only used for persistent databases (cf. get_database_settings).
        We generate them for all instances to ensure that app servers can be spawned successfully
        even if an instance is edited to change 'use_ephemeral_databases' from True to False.
        """
        if not self.mysql_user:
            self.mysql_user = get_random_string(length=16, allowed_chars=string.ascii_lowercase)
            self.mysql_pass = get_random_string(length=32)
        if not self.mongo_user:
            self.mongo_user = get_random_string(length=16, allowed_chars=string.ascii_lowercase)
            self.mongo_pass = get_random_string(length=32)

    def get_database_settings(self):
        """
        Get configuration_database_settings to pass to a new AppServer

        Only needed when not using ephemeral databases
        """
        if self.use_ephemeral_databases:
            return ''

        new_settings = ''

        # MySQL:
        if settings.INSTANCE_MYSQL_URL_OBJ:
            template = loader.get_template('instance/ansible/mysql.yml')
            new_settings += template.render({
                'user': self.mysql_user,
                'pass': self.mysql_pass,
                'host': settings.INSTANCE_MYSQL_URL_OBJ.hostname,
                'port': settings.INSTANCE_MYSQL_URL_OBJ.port or 3306,
                'database': self.mysql_database_name
            })

        # MongoDB:
        if settings.INSTANCE_MONGO_URL_OBJ:
            template = loader.get_template('instance/ansible/mongo.yml')
            new_settings += template.render({
                'user': self.mongo_user,
                'pass': self.mongo_pass,
                'host': settings.INSTANCE_MONGO_URL_OBJ.hostname,
                'port': settings.INSTANCE_MONGO_URL_OBJ.port or 27017,
                'database': self.mongo_database_name,
                'forum_database': self.forum_database_name
            })

        return new_settings
