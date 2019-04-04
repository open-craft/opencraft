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
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction
from django_extensions.db.models import TimeStampedModel

from instance.models.shared_server import SharedServerManager
from .utils import ValidateModelMixin


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Constants ###################################################################

MYSQL_SERVER_DEFAULT_PORT = 3306
MONGODB_SERVER_DEFAULT_PORT = 27017


# Models ######################################################################


class DatabaseServerManager(SharedServerManager):
    """
    Custom manager for the DatabaseServer model.
    """

    def extra_args(self, host, primary, replica_set):  # pylint: disable=no-self-use
        """
        Return extra attributes needed for database creation
        """
        return {}

    def create_database_server(self, host=None, user=None, password=None, port=None,
                               primary=None, replica_set=None):
        """
        Create database server
        """
        logger.info("Creating DatabaseServer %s", host)
        extra_args = self.extra_args(host, primary, replica_set)
        self.update_or_create(
            hostname=host,
            defaults=dict(
                name=host,
                username=user,
                password=password,
                port=port,
                accepts_new_clients=True,
                **extra_args
            ),
        )

    def _create_default(self):
        """
        Create the default database server configured in the Django settings, if any.
        """
        database_server_url = getattr(settings, self.model.DEFAULT_SETTINGS_NAME, None)
        if database_server_url:
            database_server_url_obj = urlparse(database_server_url)
            hostname, username, password, port = (
                database_server_url_obj.hostname,
                database_server_url_obj.username or '',
                database_server_url_obj.password or '',
                database_server_url_obj.port or None,
            )
            if not hostname:
                raise ImproperlyConfigured(
                    "{setting_name} must specify at least host name of database server.".format(
                        setting_name=self.model.DEFAULT_SETTINGS_NAME
                    )
                )
            self.create_database_server(host=hostname, user=username, password=password, port=port)


class DatabaseServer(ValidateModelMixin, TimeStampedModel):
    """
    DatabaseServer: Abstract parent class for database server models.
    """
    objects = DatabaseServerManager()

    class Meta:
        abstract = True

    # Human readable identifier for database instances
    name = models.CharField(max_length=250, blank=False)
    description = models.CharField(max_length=250, blank=True)

    # Host name or IP address of this database server
    hostname = models.CharField(max_length=128, unique=True)

    # Port to use when accessing this database server
    port = models.PositiveIntegerField(blank=True)

    # Credentials for accessing this database server.
    # User identified by these credentials must have necessary permissions
    # to create databases, create users, grant privileges on this database server.
    username = models.CharField(max_length=64, blank=True)
    password = models.CharField(max_length=128, blank=True)

    # Does this database server currently accept new clients (i.e., instances)?
    accepts_new_clients = models.BooleanField(default=False)

    @property
    def protocol(self):
        """
        Protocol to use for accessing this database server.
        """
        raise NotImplementedError("Specific database server implementations must define this.")

    @property
    def default_port(self):
        """
        Default port for this database server.
        """
        raise NotImplementedError("Specific database server implementations must define this.")

    @property
    def url(self):
        """
        Full URL for this database server.
        """
        url = '{protocol}://'.format(protocol=self.protocol)
        if self.username:
            url += self.username
            if self.password:
                url += ':{password}'.format(password=self.password)
            url += '@'
        url += self.hostname
        if not self.port == self.default_port:
            url += ':{port}'.format(port=self.port)
        return url

    def __str__(self):
        description = ''
        if self.description:
            description = ' ({description})'.format(description=self.description)
        return '{name}{description}'.format(
            name=self.name,
            description=description
        )

    def settings_match(self, username, password, port):
        """
        Return True if settings of this database server match settings passed to this method, else False.

        If caller did not specify `port`, compare using default port for this database server.
        """
        if port is None:
            port = self.default_port
        return self.username == username and self.password == password and self.port == port

    def save(self, **kwargs):
        """
        Set default port before saving.
        """
        if not self.port:
            self.port = self.default_port
        super().save(**kwargs)


class MySQLServer(DatabaseServer):
    """
    MySQLServer: Represents a MySQL server to be used by one or more instances.
    """
    # Name of Django setting specifying field defaults for MySQL database server (in the form of a URL).
    DEFAULT_SETTINGS_NAME = "DEFAULT_INSTANCE_MYSQL_URL"

    class Meta:
        verbose_name = 'MySQL server'

    @property
    def protocol(self):
        return 'mysql'

    @property
    def default_port(self):
        return MYSQL_SERVER_DEFAULT_PORT


class MongoDBReplicaSetManager(models.Manager):
    """
    Custom manager for the DatabaseServer model.
    """
    def extra_args(self, host, primary, replica_set):  # pylint: disable=no-self-use
        """
        Return extra attributes needed for database creation
        """
        primary = host == primary
        return dict(
            replica_set=replica_set,
            primary=primary
        )

    def _get_setting(self, field):
        """
        Get setting using prefix
        """
        return getattr(
            settings,
            self._get_setting_name(field),
            None
        )

    def _get_setting_name(self, field):
        """
        Get setting name for field
        """
        return self.model.DEFAULT_SETTINGS_NAME + '_' + field.upper()

    def get_replica_set_settings(self):
        """
        Create dictionary with replica settings
        """
        return {
            'user': self._get_setting('user'),
            'password': self._get_setting('password'),
            'name': self._get_setting('name'),
            'primary': self._get_setting('primary'),
            'hosts': self._get_setting('hosts'),
            'port': self._get_setting('port')
        }

    def _create_default(self):
        """
        Create the default database replica set configured in the Django settings, if any.
        """
        optional_settings = ['port']
        replica_settings = self.get_replica_set_settings()
        for setting in replica_settings:
            if setting not in optional_settings and replica_settings[setting] is None:
                raise ImproperlyConfigured(
                    "Error creating the default servers for the replica set, please set"
                    " {}.".format(self._get_setting_name(setting))
                )
        replica_set_hosts = [host.strip() for host in replica_settings['hosts'].split(',')]
        replica_set, _ = self.get_or_create(name=replica_settings['name'])
        for host in replica_set_hosts:
            MongoDBServer.objects.create_database_server(
                host=host,
                user=replica_settings['user'],
                password=replica_settings['password'],
                port=replica_settings['port'],
                primary=replica_settings['primary'],
                replica_set=replica_set
            )

    def select_random(self):
        """
        Select a replica set for a new instance.
        The current implementation selects one of the replica sets with servers that accept new clients at random.
        If no database server accepts new clients, DoesNotExist is raised.
        """
        self._create_default()

        # The set of servers might change between retrieving the server count and retrieving the random server,
        # so we make this atomic.
        with transaction.atomic():
            mongodb_servers = MongoDBServer.objects.filter(
                replica_set__isnull=False,
                accepts_new_clients=True,
                primary=True
            ).distinct().select_related('replica_set')
            logger.error(mongodb_servers)
            count = mongodb_servers.count()
            if not count:
                raise self.model.DoesNotExist(
                    "No server from the replica sets configured accepts new clients."
                )
            return mongodb_servers[random.randrange(count)].replica_set


class MongoDBReplicaSet(TimeStampedModel):
    """
    MongoDBServer: Represents a MongoDB Replica Set to be used by one or more instances.
    """
    DEFAULT_SETTINGS_NAME = 'DEFAULT_MONGO_REPLICA_SET'

    # Human readable identifier for MongoDB Replica Sets
    name = models.CharField(
        max_length=250,
        blank=True,
        help_text='Must match name in replicaset_name on a MongoDB server.'
    )
    description = models.CharField(max_length=250, blank=True)
    objects = MongoDBReplicaSetManager()

    class Meta:
        verbose_name = 'MongoDB Replica Set'

    def __str__(self):
        description = ''
        if self.description:
            description = ' ({description})'.format(description=self.description)
        return '{name}{description}'.format(
            name=self.name,
            description=description
        )


class MongoDBServerManager(DatabaseServerManager):
    """
    MongoDB Server Manager
    """
    def extra_args(self, host, primary, replica_set):
        """
        Return extra attributes needed for database creation
        """
        primary = host == primary
        return dict(
            replica_set=replica_set,
            primary=primary
        )


class MongoDBServer(DatabaseServer):
    """
    MongoDBServer: Represents a MongoDB server to be used by one or more instances.
    """
    # Name of Django setting specifying field defaults for MongoDB database server (in the form of a URL).
    DEFAULT_SETTINGS_NAME = "DEFAULT_INSTANCE_MONGO_URL"

    replica_set = models.ForeignKey(
        MongoDBReplicaSet,
        null=True,
        blank=True,
        help_text="Replica Set to which the server belongs."
    )
    primary = models.BooleanField(
        default=False,
        help_text=(
            "Indicates if the server is the primary server on a Replica Set, "
            "only applies when replica_set is set."
        )
    )

    objects = MongoDBServerManager()

    class Meta:
        verbose_name = 'MongoDB server'

    @property
    def protocol(self):
        return 'mongodb'

    @property
    def default_port(self):
        return MONGODB_SERVER_DEFAULT_PORT
