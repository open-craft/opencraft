# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <xavier@opencraft.com>
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
import hashlib
import hmac
import yaml

from instance.models.mixins.database import MySQLInstanceMixin, MongoDBInstanceMixin
from instance.models.mixins.rabbitmq import RabbitMQInstanceMixin


# Classes #####################################################################

class OpenEdXDatabaseMixin(MySQLInstanceMixin, MongoDBInstanceMixin, RabbitMQInstanceMixin):
    """
    Mixin that provides functionality required for the database backends that an
    OpenEdX Instance uses

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
                "user": self._get_mysql_user_name("ecommerce"),
            },
            {
                "name": self._get_mysql_database_name("dashboard"),
                "user": self._get_mysql_user_name("dashboard"),
            },
            {
                "name": self._get_mysql_database_name("xqueue"),
                "user": self._get_mysql_user_name("xqueue"),
            },
            {
                "name": self._get_mysql_database_name("edxapp"),
                "user": self._get_mysql_user_name("edxapp"),
            },
            {
                "name": self._get_mysql_database_name("edxapp_csmh"),
                "user": self._get_mysql_user_name("edxapp"),
            },
            {
                "name": self._get_mysql_database_name("edx_notes_api"),
                "user": self._get_mysql_user_name("notes"),
                "priv": "SELECT,INSERT,UPDATE,DELETE",
            },
            {
                "name": self._get_mysql_database_name("notifier"),
                "user": self._get_mysql_user_name("notifier"),
            },
            {
                "name": self._get_mysql_database_name("analytics_api"),
                "user": self._get_mysql_user_name("api"),
            },
            {
                "name": self._get_mysql_database_name("discovery"),
                "user": self._get_mysql_user_name("discovery"),
            },
            {
                "name": self._get_mysql_database_name("reports"),
                "user": self._get_mysql_user_name("reports"),
                "priv": "SELECT",
                "additional_users": [
                    {
                        "name": self._get_mysql_user_name("api"),
                        "priv": "SELECT",
                    }
                ],
            },
            {
                "name": self._get_mysql_database_name("programs"),
                "user": self._get_mysql_user_name("program"),
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
        Build unique name for MySQL database using suffix.

        To generate a unique name, this method adds an underscore and the specified suffix
        to the database_name of this instance.

        database_name can be up to 50 characters long.
        The maximum length for the name of a MySQL database is 64 characters.
        To ensure that the generated name does not exceed that length,
        suffix should not consist of more than 13 characters.
        """
        mysql_database_name = "{0}_{1}".format(self.mysql_database_name, suffix)
        assert len(mysql_database_name) <= 64
        return mysql_database_name

    def get_mysql_cursor_for_db(self, db_suffix):
        """
        Get an adminstrative cursor with which to execute queries on the database
        for the application linked to the provided db_suffix.
        """
        if not self.mysql_server:
            return None
        import MySQLdb as mysql
        db_name = self._get_mysql_database_name(db_suffix)
        conn = mysql.connect(
            host=self.mysql_server.hostname,
            user=self.mysql_server.username,
            passwd=self.mysql_server.password,
            port=self.mysql_server.port,
            database=db_name,
        )
        return conn.cursor()

    def _get_mysql_user_name(self, suffix):
        """
        Build unique name for MySQL user using suffix.

        To generate a unique name, this method adds an underscore and the specified suffix
        to the mysql_user of this instance.

        mysql_user is 6 characters long.
        The maximum length of usernames in MySQL is 16 characters.
        To ensure that the generated name does not exceed that length,
        suffix must not consist of more than 9 characters.
        """
        mysql_user_name = "{0}_{1}".format(self.mysql_user, suffix)
        assert len(mysql_user_name) <= 16
        return mysql_user_name

    def _get_mysql_pass(self, user):
        """
        Build unique password for user, derived from MySQL password for this instance and user.
        """
        encoding = "utf-8"
        key = bytes(source=self.mysql_pass, encoding=encoding)
        msg = bytes(source=user, encoding=encoding)
        return hmac.new(key, msg=msg, digestmod=hashlib.sha256).hexdigest()

    def _get_mysql_pass_from_dbname(self, dbname):
        """
        Returns the mysql password for the user configured for database of `dbname`
        """
        user = self._get_mysql_user_name(dbname)
        return self._get_mysql_pass(user)

    def _get_mysql_settings(self):
        """
        Return dictionary of settings for mysql databases
        """
        return {
            # edxapp
            "EDXAPP_MYSQL_DB_NAME": self._get_mysql_database_name("edxapp"),
            "EDXAPP_MYSQL_USER": self._get_mysql_user_name("edxapp"),
            "EDXAPP_MYSQL_PASSWORD": self._get_mysql_pass_from_dbname("edxapp"),
            "EDXAPP_MYSQL_HOST": self.mysql_server.hostname,
            "EDXAPP_MYSQL_PORT": self.mysql_server.port,

            # ecommerce
            "ECOMMERCE_DATABASE_NAME": self._get_mysql_database_name("ecommerce"),
            "ECOMMERCE_DATABASE_USER": self._get_mysql_user_name("ecommerce"),
            "ECOMMERCE_DATABASE_PASSWORD": self._get_mysql_pass_from_dbname("ecommerce"),
            "ECOMMERCE_DATABASE_HOST": self.mysql_server.hostname,

            # Old ecommerce database settings kept around for compatibility with Ginkgo.
            "ECOMMERCE_DEFAULT_DB_NAME": "{{ ECOMMERCE_DATABASE_NAME }}",
            "ECOMMERCE_DATABASES": {
                "default": {
                    "ENGINE": 'django.db.backends.mysql',
                    "NAME": "{{ ECOMMERCE_DATABASE_NAME }}",
                    "USER": "{{ ECOMMERCE_DATABASE_USER }}",
                    "PASSWORD": "{{ ECOMMERCE_DATABASE_PASSWORD }}",
                    "HOST": "{{ ECOMMERCE_DATABASE_HOST }}",
                    "PORT": self.mysql_server.port,
                    "ATOMIC_REQUESTS": True,
                    "CONN_MAX_AGE": 0
                },
            },

            # insights
            "INSIGHTS_DATABASE_NAME": self._get_mysql_database_name("dashboard"),
            "INSIGHTS_DATABASES": {
                "default": {
                    "ENGINE": 'django.db.backends.mysql',
                    "NAME": self._get_mysql_database_name("dashboard"),
                    "USER": self._get_mysql_user_name("dashboard"),
                    "PASSWORD": self._get_mysql_pass_from_dbname("dashboard"),
                    "HOST": self.mysql_server.hostname,
                    "PORT": self.mysql_server.port,
                },
            },

            # xqueue
            "XQUEUE_MYSQL_DB_NAME": self._get_mysql_database_name("xqueue"),
            "XQUEUE_MYSQL_USER": self._get_mysql_user_name("xqueue"),
            "XQUEUE_MYSQL_PASSWORD": self._get_mysql_pass_from_dbname("xqueue"),
            "XQUEUE_MYSQL_HOST": self.mysql_server.hostname,
            "XQUEUE_MYSQL_PORT": self.mysql_server.port,

            # edxapp_csmh
            "EDXAPP_MYSQL_CSMH_DB_NAME": self._get_mysql_database_name("edxapp_csmh"),
            "EDXAPP_MYSQL_CSMH_USER": self._get_mysql_user_name("edxapp"),
            "EDXAPP_MYSQL_CSMH_PASSWORD": self._get_mysql_pass_from_dbname("edxapp"),
            "EDXAPP_MYSQL_CSMH_HOST": self.mysql_server.hostname,
            "EDXAPP_MYSQL_CSMH_PORT": self.mysql_server.port,

            # edx_notes_api
            "EDX_NOTES_API_MYSQL_DB_NAME": self._get_mysql_database_name("edx_notes_api"),
            "EDX_NOTES_API_MYSQL_DB_USER": self._get_mysql_user_name("notes"),
            "EDX_NOTES_API_MYSQL_DB_PASS": self._get_mysql_pass_from_dbname("notes"),
            "EDX_NOTES_API_MYSQL_HOST": self.mysql_server.hostname,

            # notifier
            "NOTIFIER_DATABASE_ENGINE": 'django.db.backends.mysql',
            "NOTIFIER_DATABASE_NAME": self._get_mysql_database_name("notifier"),
            "NOTIFIER_DATABASE_USER": self._get_mysql_user_name("notifier"),
            "NOTIFIER_DATABASE_PASSWORD": self._get_mysql_pass_from_dbname("notifier"),
            "NOTIFIER_DATABASE_HOST": self.mysql_server.hostname,
            "NOTIFIER_DATABASE_PORT": self.mysql_server.port,

            # programs
            "PROGRAMS_DEFAULT_DB_NAME": self._get_mysql_database_name("programs"),
            "PROGRAMS_DATABASES": {
                "default": {
                    "ENGINE": 'django.db.backends.mysql',
                    "NAME": self._get_mysql_database_name("programs"),
                    "USER": self._get_mysql_user_name("program"),
                    "PASSWORD": self._get_mysql_pass_from_dbname("program"),
                    "HOST": self.mysql_server.hostname,
                    "PORT": self.mysql_server.port,
                    "ATOMIC_REQUESTS": True,
                    "CONN_MAX_AGE": 0
                },
            },

            # analytics_api
            "ANALYTICS_API_DEFAULT_DB_NAME": self._get_mysql_database_name("analytics_api"),
            "ANALYTICS_API_REPORTS_DB_NAME": self._get_mysql_database_name("reports"),
            "ANALYTICS_API_DATABASES": {
                "default": {
                    "ENGINE": 'django.db.backends.mysql',
                    "NAME": self._get_mysql_database_name("analytics_api"),
                    "USER": self._get_mysql_user_name("api"),
                    "PASSWORD": self._get_mysql_pass_from_dbname("api"),
                    "HOST": self.mysql_server.hostname,
                    "PORT": self.mysql_server.port,
                },
                "reports": {
                    "ENGINE": 'django.db.backends.mysql',
                    "NAME": self._get_mysql_database_name("reports"),
                    "USER": self._get_mysql_user_name("reports"),
                    "PASSWORD": self._get_mysql_pass_from_dbname("reports"),
                    "HOST": self.mysql_server.hostname,
                    "PORT": self.mysql_server.port,
                },
            },

            # course discovery api
            "DISCOVERY_MYSQL": self.mysql_server.hostname,
            "DISCOVERY_DEFAULT_DB_NAME": self._get_mysql_database_name("discovery"),
            "DISCOVERY_MYSQL_USER": self._get_mysql_user_name("discovery"),
            "DISCOVERY_MYSQL_PASSWORD": self._get_mysql_pass_from_dbname("discovery"),

            # Common users
            "COMMON_MYSQL_MIGRATE_USER": self.migrate_user,
            "COMMON_MYSQL_MIGRATE_PASS": self._get_mysql_pass(self.migrate_user),
            "COMMON_MYSQL_READ_ONLY_USER": self.read_only_user,
            "COMMON_MYSQL_READ_ONLY_PASS": self._get_mysql_pass(self.read_only_user),
            "COMMON_MYSQL_ADMIN_USER": self.admin_user,
            "COMMON_MYSQL_ADMIN_PASS": self._get_mysql_pass(self.admin_user),

            # Common options to all django services
            "edx_django_service_default_db_conn_max_age": 0,
        }

    def _get_mongo_settings(self):
        """
        Return dictionary of mongodb settings
        """
        extra_settings = {}
        primary_mongodb_server = self.primary_mongodb_server
        edxapp_mongo_hosts = ''

        # Upstream Ginkgo (and previous) releases do not support replicasets, and require a list of hostnames.
        # OpenCraft backported replicaset support into Ginkgo release branches.
        if (("ginkgo" in self.openedx_release and "opencraft" not in self.configuration_version) or
                "ficus" in self.openedx_release):
            edxapp_mongo_hosts = [primary_mongodb_server.hostname]  # pylint: disable=redefined-variable-type

        # Replicasets are supported by OpenCraft's ginkgo, and upstream post-Ginkgo releases, and require a
        # comma-separated string of hostnames.
        elif self.mongodb_replica_set:
            edxapp_mongo_hosts = ",".join(self.mongodb_servers.values_list('hostname', flat=True))
            extra_settings = {
                "EDXAPP_MONGO_REPLICA_SET": self.mongodb_replica_set.name
            }
        # If no replicaset is configured, use just the primary hostname
        else:
            edxapp_mongo_hosts = primary_mongodb_server.hostname

        settings = {
            "EDXAPP_MONGO_USER": self.mongo_user,
            "EDXAPP_MONGO_PASSWORD": self.mongo_pass,
            "EDXAPP_MONGO_HOSTS": edxapp_mongo_hosts,
            "EDXAPP_MONGO_PORT": primary_mongodb_server.port,
            "EDXAPP_MONGO_DB_NAME": self.mongo_database_name,
            # Forum doesn't support replicasets, so just use primary host
            "FORUM_MONGO_USER": self.mongo_user,
            "FORUM_MONGO_PASSWORD": self.mongo_pass,
            "FORUM_MONGO_HOSTS": [primary_mongodb_server.hostname],
            "FORUM_MONGO_PORT": primary_mongodb_server.port,
            "FORUM_MONGO_DATABASE": self.forum_database_name,
            "FORUM_REBUILD_INDEX": True
        }
        settings.update(extra_settings)
        return settings

    def _get_rabbitmq_settings(self):
        """
        Return dictionary of RabbitMQ Settings
        """
        return {
            "XQUEUE_RABBITMQ_USER": self.rabbitmq_provider_user.username,
            "XQUEUE_RABBITMQ_PASS": self.rabbitmq_provider_user.password,
            "XQUEUE_RABBITMQ_VHOST": self.rabbitmq_vhost,
            "XQUEUE_RABBITMQ_HOSTNAME": self.rabbitmq_server.instance_host,
            "XQUEUE_RABBITMQ_PORT": self.rabbitmq_server.instance_port,
            "XQUEUE_RABBITMQ_TLS": True,
            "XQUEUE_SESSION_ENGINE": "django.contrib.sessions.backends.cache",
            "XQUEUE_CACHES": {
                "default": {
                    "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
                    "KEY_PREFIX": "xqueue",
                    "LOCATION": "{{ EDXAPP_MEMCACHE }}",
                },
            },

            "EDXAPP_CELERY_USER": self.rabbitmq_provider_user.username,
            "EDXAPP_CELERY_PASSWORD": self.rabbitmq_provider_user.password,
            "EDXAPP_CELERY_BROKER_VHOST": self.rabbitmq_vhost,
            "EDXAPP_RABBIT_HOSTNAME": "{}:{}".format(
                self.rabbitmq_server.instance_host,
                self.rabbitmq_server.instance_port
            ),
            "EDXAPP_CELERY_BROKER_USE_SSL": True
        }

    def get_database_settings(self):
        """
        Get configuration_database_settings to pass to a new AppServer
        """
        new_settings = {}

        # MySQL:
        if self.mysql_server:
            new_settings.update(self._get_mysql_settings())

        # MongoDB:
        if self.mongodb_replica_set or self.mongodb_server:
            new_settings.update(self._get_mongo_settings())

        # RabbitMQ:
        new_settings.update(self._get_rabbitmq_settings())

        return yaml.dump(new_settings, default_flow_style=False)
