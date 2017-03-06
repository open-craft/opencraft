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
DatabaseServer models - tests
"""

# Imports #####################################################################

from urllib.parse import urlparse

import ddt
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import override_settings

from instance.models.database_server import (
    MYSQL_SERVER_DEFAULT_PORT, MONGODB_SERVER_DEFAULT_PORT, MySQLServer, MongoDBServer
)
from instance.models.log_entry import LogEntry
from instance.tests.base import TestCase
from instance.tests.models.factories.database_server import MySQLServerFactory, MongoDBServerFactory


# Classes #####################################################################

@ddt.ddt
class MySQLServerTest(TestCase):
    """
    Test cases for the MySQLServer model.
    """
    def setUp(self):
        self.mysql_server = MySQLServerFactory()

    def test_default_settings_name(self):
        """
        Test that MySQLServer defines `DEFAULT_SETTINGS_NAME` field with appropriate value.
        """
        try:
            default_settings_name = MySQLServer.DEFAULT_SETTINGS_NAME
        except AttributeError:
            self.fail('MySQLServer must define `DEFAULT_SETTINGS_NAME` field.')
        else:
            self.assertEqual(default_settings_name, 'DEFAULT_INSTANCE_MYSQL_URL')

    def test_protocol(self):
        """
        Test that `protocol` property returns correct value.
        """
        self.assertEqual(self.mysql_server.protocol, 'mysql')

    @ddt.data(
        (None, 'user', 'pass', 'mysql://user:pass@mysql-server'),
        (None, 'user', None, 'mysql://user@mysql-server'),
        (None, None, 'pass', 'mysql://mysql-server'),
        (None, None, None, 'mysql://mysql-server'),
        (1234, 'user', 'pass', 'mysql://user:pass@mysql-server:1234'),
        (1234, 'user', None, 'mysql://user@mysql-server:1234'),
        (1234, None, 'pass', 'mysql://mysql-server:1234'),
        (1234, None, None, 'mysql://mysql-server:1234'),
    )
    @ddt.unpack
    def test_url(self, port, username, password, expected_url):
        """
        Test that `url` property returns correct URL.
        """
        self.mysql_server.hostname = 'mysql-server'
        if port:
            self.mysql_server.port = port
        if username:
            self.mysql_server.username = username
        if password:
            self.mysql_server.password = password
        self.mysql_server.save()
        self.assertEqual(self.mysql_server.url, expected_url)

    @ddt.data(
        (None, 'user', 'pass', True),
        (None, 'user', 'word', False),
        (None, 'name', 'pass', False),
        (None, 'name', 'word', False),
        (1234, 'user', 'pass', True),
        (1234, 'user', 'word', False),
        (1234, 'name', 'pass', False),
        (1234, 'name', 'word', False),
        (5678, 'user', 'pass', False),
        (5678, 'user', 'word', False),
        (5678, 'name', 'pass', False),
        (5678, 'name', 'word', False),
    )
    @ddt.unpack
    def test_settings_match(self, port, username, password, expected_result):
        """
        Test that `settings_match` method correctly reports whether settings of a MySQL server
        match the settings passed to the method.
        """
        # If caller does not specify `port`, `settings_match` should compare
        # port of MySQL server to `MYSQL_SERVER_DEFAULT_PORT`,
        # so only set port on MySQL server if it is not `None`.
        if port:
            self.mysql_server.port = 1234
        self.mysql_server.username = 'user'
        self.mysql_server.password = 'pass'
        self.mysql_server.save()
        self.assertEqual(self.mysql_server.settings_match(username, password, port), expected_result)

    def test_set_field_defaults(self):
        """
        Test that `set_field_defaults` sets port to `MYSQL_SERVER_DEFAULT_PORT` if not specified.

        The `set_field_defaults` method is called when a MySQLServer is first created.
        """
        default_mysql_server = MySQLServerFactory()
        self.assertEqual(default_mysql_server.port, MYSQL_SERVER_DEFAULT_PORT)
        custom_mysql_server = MySQLServerFactory(port=1234)
        self.assertEqual(custom_mysql_server.port, 1234)


@ddt.ddt
class MongoDBServerTest(TestCase):
    """
    Test cases for the MongoDBServer model.
    """
    def setUp(self):
        self.mongodb_server = MongoDBServerFactory()

    def test_default_settings_name(self):
        """
        Test that MongoDBServer defines `DEFAULT_SETTINGS_NAME` field with appropriate value.
        """
        try:
            default_settings_name = MongoDBServer.DEFAULT_SETTINGS_NAME
        except AttributeError:
            self.fail('MongoDBServer must define `DEFAULT_SETTINGS_NAME` field.')
        else:
            self.assertEqual(default_settings_name, 'DEFAULT_INSTANCE_MONGO_URL')

    def test_protocol(self):
        """
        Test that `protocol` property returns correct value.
        """
        self.assertEqual(self.mongodb_server.protocol, 'mongodb')

    @ddt.data(
        (None, 'user', 'pass', 'mongodb://user:pass@mongodb-server'),
        (None, 'user', None, 'mongodb://user@mongodb-server'),
        (None, None, 'pass', 'mongodb://mongodb-server'),
        (None, None, None, 'mongodb://mongodb-server'),
        (1234, 'user', 'pass', 'mongodb://user:pass@mongodb-server:1234'),
        (1234, 'user', None, 'mongodb://user@mongodb-server:1234'),
        (1234, None, 'pass', 'mongodb://mongodb-server:1234'),
        (1234, None, None, 'mongodb://mongodb-server:1234'),
    )
    @ddt.unpack
    def test_url(self, port, username, password, expected_url):
        """
        Test that `url` property returns correct URL.
        """
        self.mongodb_server.hostname = 'mongodb-server'
        if port:
            self.mongodb_server.port = port
        if username:
            self.mongodb_server.username = username
        if password:
            self.mongodb_server.password = password
        self.mongodb_server.save()
        self.assertEqual(self.mongodb_server.url, expected_url)

    @ddt.data(
        (None, 'user', 'pass', True),
        (None, 'user', 'word', False),
        (None, 'name', 'pass', False),
        (None, 'name', 'word', False),
        (1234, 'user', 'pass', True),
        (1234, 'user', 'word', False),
        (1234, 'name', 'pass', False),
        (1234, 'name', 'word', False),
        (5678, 'user', 'pass', False),
        (5678, 'user', 'word', False),
        (5678, 'name', 'pass', False),
        (5678, 'name', 'word', False),
    )
    @ddt.unpack
    def test_settings_match(self, port, username, password, expected_result):
        """
        Test that `settings_match` method correctly reports whether settings of a MongoDB server
        match the settings passed to the method.
        """
        # If caller does not specify `port`, `settings_match` should compare
        # port of MySQL server to `MYSQL_SERVER_DEFAULT_PORT`,
        # so only set port on MySQL server if it is not `None`.
        if port:
            self.mongodb_server.port = 1234
        self.mongodb_server.username = 'user'
        self.mongodb_server.password = 'pass'
        self.mongodb_server.save()
        self.assertEqual(self.mongodb_server.settings_match(username, password, port), expected_result)

    def test_set_field_defaults(self):
        """
        Test that `set_field_defaults` sets port to `MONGODB_SERVER_DEFAULT_PORT` if not specified.

        The `set_field_defaults` method is called when a MongoDBServer is first created.
        """
        default_mongodb_server = MongoDBServerFactory()
        self.assertEqual(default_mongodb_server.port, MONGODB_SERVER_DEFAULT_PORT)
        custom_mongodb_server = MongoDBServerFactory(port=1234)
        self.assertEqual(custom_mongodb_server.port, 1234)


class DatabaseServerManagerTest(TestCase):
    """
    Test cases for DatabaseServerManager.
    """
    def _assert_settings(self, database_server, **expected_settings):
        """
        Assert that `database_server` settings match `expected_settings`.
        """
        for setting, value in expected_settings.items():
            self.assertEqual(getattr(database_server, setting), value)

    def _assert_default_settings(self, mysql_server, mongodb_server):
        """
        Assert that settings of `mysql_server` and `mongodb_server` match default settings.
        """
        mysql_url_obj = urlparse(settings.DEFAULT_INSTANCE_MYSQL_URL)
        mongodb_url_obj = urlparse(settings.DEFAULT_INSTANCE_MONGO_URL)

        self._assert_settings(
            mysql_server,
            name=mysql_url_obj.hostname,
            hostname=mysql_url_obj.hostname,
            username=mysql_url_obj.username or '',
            password=mysql_url_obj.password or '',
            port=mysql_url_obj.port or MYSQL_SERVER_DEFAULT_PORT,
        )
        self._assert_settings(
            mongodb_server,
            name=mysql_url_obj.hostname,
            hostname=mongodb_url_obj.hostname,
            username=mongodb_url_obj.username or '',
            password=mongodb_url_obj.password or '',
            port=mysql_url_obj.port or MONGODB_SERVER_DEFAULT_PORT,
        )

    @override_settings(
        DEFAULT_INSTANCE_MYSQL_URL='mysql-server-no-hostname',
        DEFAULT_INSTANCE_MONGO_URL='mongodb-server-no-hostname',
    )
    def test_invalid_default_settings(self):
        """
        Test that `get_random` raises an exception when default settings for MySQL and MongoDB servers
        do not specify a hostname.
        """
        with self.assertRaises(ImproperlyConfigured):
            MySQLServer.objects.select_random()
        with self.assertRaises(ImproperlyConfigured):
            MongoDBServer.objects.select_random()

    def test_select_random(self):
        """
        Test that `select_random` returns MySQL and MongoDB servers created from default settings
        if no MySQLServer and no MongoDBServer objects are available.
        """
        mysql_server = MySQLServer.objects.select_random()
        mongodb_server = MongoDBServer.objects.select_random()

        self._assert_default_settings(mysql_server, mongodb_server)

    def test__create_default(self):
        """
        Test that `_create_default` uses default settings to create MySQL and MongoDB servers.
        """
        MySQLServer.objects._create_default()
        MongoDBServer.objects._create_default()

        self.assertEqual(MySQLServer.objects.count(), 1)
        self.assertEqual(MongoDBServer.objects.count(), 1)

        mysql_server = MySQLServer.objects.get()
        mongodb_server = MongoDBServer.objects.get()

        self._assert_default_settings(mysql_server, mongodb_server)

    def test__create_default_exists_settings_match(self):
        """
        Test that `_create_default` does not create new database server and does not log warning
        if database server with identical settings already exists.
        """
        mysql_hostname = urlparse(settings.DEFAULT_INSTANCE_MYSQL_URL).hostname
        mongodb_hostname = urlparse(settings.DEFAULT_INSTANCE_MONGO_URL).hostname

        MySQLServer.objects._create_default()
        MongoDBServer.objects._create_default()

        # Precondition
        self.assertEqual(MySQLServer.objects.count(), 1)
        self.assertEqual(MongoDBServer.objects.count(), 1)

        MySQLServer.objects._create_default()
        MongoDBServer.objects._create_default()

        # Number of database servers should not have changed
        self.assertEqual(MySQLServer.objects.count(), 1)
        self.assertEqual(MongoDBServer.objects.count(), 1)

        log_entries = LogEntry.objects.all()
        self.assertFalse(any(
            'DatabaseServer for {hostname} already exists, '
            'and its settings do not match the Django settings'.format(hostname=mysql_hostname) in log_entry.text
            for log_entry in log_entries
        ))
        self.assertFalse(any(
            'DatabaseServer for {hostname} already exists, '
            'and its settings do not match the Django settings'.format(hostname=mongodb_hostname) in log_entry.text
            for log_entry in log_entries
        ))

    def test__create_default_exists_settings_differ(self):
        """
        Test that `_create_default` does not create new database server and logs warning
        if database server with same hostname but different username, password, port already exists.
        """
        mysql_hostname = urlparse(settings.DEFAULT_INSTANCE_MYSQL_URL).hostname
        mongodb_hostname = urlparse(settings.DEFAULT_INSTANCE_MONGO_URL).hostname

        MySQLServer.objects._create_default()
        MongoDBServer.objects._create_default()

        # Precondition
        self.assertEqual(MySQLServer.objects.count(), 1)
        self.assertEqual(MongoDBServer.objects.count(), 1)

        with override_settings(
            DEFAULT_INSTANCE_MYSQL_URL='mysql://user:pass@{hostname}'.format(hostname=mysql_hostname),
            DEFAULT_INSTANCE_MONGO_URL='mongodb://user:pass@{hostname}'.format(hostname=mongodb_hostname),
        ):
            MySQLServer.objects._create_default()
            MongoDBServer.objects._create_default()

        # Number of database servers should not have changed
        self.assertEqual(MySQLServer.objects.count(), 1)
        self.assertEqual(MongoDBServer.objects.count(), 1)

        # Log entries should contain two warnings about existing servers with different settings
        log_entries = LogEntry.objects.all()
        mysql_warning = (
            'DatabaseServer for {hostname} already exists, '
            'and its settings do not match the Django settings'.format(hostname=mysql_hostname)
        )
        if mysql_hostname == mongodb_hostname:
            self.assertEqual(len([
                log_entry for log_entry in log_entries if mysql_warning in log_entry.text
            ]), 2)
        else:
            mongodb_warning = (
                'DatabaseServer for {hostname} already exists, '
                'and its settings do not match the Django settings'.format(hostname=mongodb_hostname)
            )
            self.assertEqual(len([
                log_entry for log_entry in log_entries if mysql_warning in log_entry.text
            ]), 1)
            self.assertEqual(len([
                log_entry for log_entry in log_entries if mongodb_warning in log_entry.text
            ]), 1)

    def test__create_default_ignores_name(self):
        """
        Test that `_create_default` does not create new database server
        if there is an existing database server with the default hostname and a name
        that does not match the default hostname.

        `_create_default` used to call `get_or_create` like this:

        database_server, created = self.get_or_create(
            name=hostname,
            hostname=hostname,
            defaults=dict(
                ...
            )
        )

        Under the circumstances described above, this was causing a ValidationError for `hostname`:
        Since `name` of the existing database server did not match `hostname`,
        Django would try to create a new database server, which would fail
        because `hostname` needs to be unique across database server objects.

        Now, `_create_default` calls `get_or_create` like this:

        database_server, created = self.get_or_create(
            hostname=hostname,
            defaults=dict(
                name=hostname,
                ...
            )
        )

        This means that new database servers will still get their `name` set to `hostname` by default,
        but the `name` field will be ignored when checking whether to create a new database server.
        """
        MySQLServer.objects._create_default()
        MongoDBServer.objects._create_default()

        # Precondition
        self.assertEqual(MySQLServer.objects.count(), 1)
        self.assertEqual(MongoDBServer.objects.count(), 1)

        # Change name of MySQLServer and MongoDBServer
        mysql_server = MySQLServer.objects.get()
        mongodb_server = MongoDBServer.objects.get()
        mysql_server.name = 'Default MySQL server'
        mongodb_server.name = 'Default MongoDB server'
        mysql_server.save()
        mongodb_server.save()

        try:
            MySQLServer.objects._create_default()
            MongoDBServer.objects._create_default()
        except ValidationError:
            self.fail(
                '_create_default should only check `hostname` of existing database servers '
                'when deciding whether to create a new database server. '
                'It should ignore `name`.'
            )
        else:
            self.assertEqual(MySQLServer.objects.count(), 1)
            self.assertEqual(MongoDBServer.objects.count(), 1)
