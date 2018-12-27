# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
OpenEdXInstance Database Mixins - Tests
"""

# Imports #####################################################################

import subprocess
from unittest.mock import patch
import urllib

import ddt
import pymongo
import responses
import yaml
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings

from instance.models.database_server import (
    MYSQL_SERVER_DEFAULT_PORT, MONGODB_SERVER_DEFAULT_PORT, MySQLServer, MongoDBServer
)
from instance.models.mixins.rabbitmq import RabbitMQAPIError
from instance.models.rabbitmq_server import RabbitMQServer
from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

class MySQLInstanceTestCase(TestCase):
    """
    Test cases for MySQLInstanceMixin and OpenEdXDatabaseMixin
    """
    def setUp(self):
        super().setUp()
        self.instance = None

    def tearDown(self):
        if self.instance:
            self.instance.deprovision_mysql()
        super().tearDown()

    def _assert_privileges(self, database):
        """
        Assert that relevant users can access database
        """
        database_name = database["name"]
        user = database["user"]
        additional_users = [user["name"] for user in database.get("additional_users", [])]
        global_users = [self.instance.migrate_user, self.instance.read_only_user]
        users = [user] + additional_users + global_users
        for user in users:
            password = self.instance._get_mysql_pass(user)
            # Pass password using MYSQL_PWD environment variable rather than the --password
            # parameter so that mysql command doesn't print a security warning.
            env = {'MYSQL_PWD': password}
            mysql_cmd = "mysql -h 127.0.0.1 -u {user} -e 'SHOW TABLES' {db_name}".format(user=user,
                                                                                         db_name=database_name)
            tables = subprocess.call(mysql_cmd, shell=True, env=env)
            self.assertEqual(tables, 0)

    def check_mysql(self):
        """
        Check that the mysql databases and users have been created
        """
        self.assertIs(self.instance.mysql_provisioned, True)
        self.assertTrue(self.instance.mysql_user)
        self.assertTrue(self.instance.mysql_pass)
        databases = subprocess.check_output("mysql -h 127.0.0.1 -u root -e 'SHOW DATABASES'", shell=True).decode()
        for database in self.instance.mysql_databases:
            # Check if database exists
            database_name = database["name"]
            self.assertIn(database_name, databases)
            # Check if relevant users can access it
            self._assert_privileges(database)

    def check_mysql_vars_not_set(self, instance):
        """
        Check that the given instance does not point to a mysql database
        """
        db_vars_str = instance.get_database_settings()
        for var in ('EDXAPP_MYSQL_USER',
                    'EDXAPP_MYSQL_PASSWORD',
                    'EDXAPP_MYSQL_HOST',
                    'EDXAPP_MYSQL_PORT',
                    'EDXAPP_MYSQL_DB_NAME',
                    'COMMON_MYSQL_MIGRATE_USER',
                    'COMMON_MYSQL_MIGRATE_PASS'):
            self.assertNotIn(var, db_vars_str)

    def check_common_users(self, instance, db_vars):
        """
        Check that instance settings contain correct information about common users.
        """
        self.assertEqual(db_vars['COMMON_MYSQL_MIGRATE_USER'], instance.migrate_user)
        self.assertEqual(db_vars['COMMON_MYSQL_MIGRATE_PASS'], instance._get_mysql_pass(instance.migrate_user))
        self.assertEqual(db_vars['COMMON_MYSQL_READ_ONLY_USER'], instance.read_only_user)
        self.assertEqual(db_vars['COMMON_MYSQL_READ_ONLY_PASS'], instance._get_mysql_pass(instance.read_only_user))
        self.assertEqual(db_vars['COMMON_MYSQL_ADMIN_USER'], instance.admin_user)
        self.assertEqual(db_vars['COMMON_MYSQL_ADMIN_PASS'], instance._get_mysql_pass(instance.admin_user))

    def check_vars(self, instance, db_vars, prefix, var_names=None, values=None):
        """
        Check that instance settings contain correct values for vars that start with prefix.
        """
        if var_names is None:
            var_names = ["DB_NAME", "USER", "PASSWORD", "HOST", "PORT"]
        instance_settings = zip(var_names, values)
        for var_name, value in instance_settings:
            var_name = prefix + var_name
            self.assertEqual(db_vars[var_name], value)

    def test__get_mysql_database_name(self):
        """
        Test that _get_mysql_database_name correctly builds database names.
        """
        self.instance = OpenEdXInstanceFactory()

        # Database name should be a combination of database_name and custom suffix
        suffix = "test"
        database_name = self.instance._get_mysql_database_name(suffix)
        expected_database_name = "{0}_{1}".format(self.instance.database_name, suffix)
        self.assertEqual(database_name, expected_database_name)

        # Using suffix that exceeds maximum length should raise an error
        suffix = "long-long-long-long-long-long-long-long-long-long-long-long-suffix"
        with self.assertRaises(AssertionError):
            self.instance._get_mysql_database_name(suffix)

    def test__get_mysql_user_name(self):
        """
        Test that _get_mysql_user_name correctly builds user names.
        """
        self.instance = OpenEdXInstanceFactory()

        # User name should be a combination of mysql_user and custom suffix
        suffix = "test"
        user_name = self.instance._get_mysql_user_name(suffix)
        expected_user_name = "{0}_{1}".format(self.instance.mysql_user, suffix)
        self.assertEqual(user_name, expected_user_name)

        # Using suffix that exceeds maximum length should raise an error
        suffix = "long-long-long-suffix"
        with self.assertRaises(AssertionError):
            self.instance._get_mysql_user_name(suffix)

    def test__get_mysql_pass(self):
        """
        Test behavior of _get_mysql_pass.

        It should:

        - generate passwords of appropriate length
        - generate different passwords for different users
        - behave deterministically, i.e., return the same password for a given user
          every time it is called with that user
        """
        self.instance = OpenEdXInstanceFactory()
        user1 = "user1"
        pass1 = self.instance._get_mysql_pass(user1)
        user2 = "user2"
        pass2 = self.instance._get_mysql_pass(user2)
        self.assertEqual(len(pass1), 64)
        self.assertEqual(len(pass2), 64)
        self.assertFalse(pass1 == pass2)
        self.assertEqual(pass1, self.instance._get_mysql_pass(user1))
        self.assertEqual(pass2, self.instance._get_mysql_pass(user2))

    def test__get_mysql_pass_from_dbname(self):
        """
        Test that _get_mysql_pass_from_dbname meets the same criteria as _get_mysql_pass
        """
        self.instance = OpenEdXInstanceFactory()
        database1 = "database1"
        pass1 = self.instance._get_mysql_pass_from_dbname(database1)
        database2 = "database2"
        pass2 = self.instance._get_mysql_pass_from_dbname(database2)
        self.assertEqual(len(pass1), 64)
        self.assertEqual(len(pass2), 64)
        self.assertFalse(pass1 == pass2)
        self.assertEqual(pass1, self.instance._get_mysql_pass_from_dbname(database1))
        self.assertEqual(pass2, self.instance._get_mysql_pass_from_dbname(database2))

    def test_provision_mysql(self):
        """
        Provision mysql database
        """
        self.instance = OpenEdXInstanceFactory()
        self.instance.provision_mysql()
        self.check_mysql()

    def test_provision_mysql_weird_domain(self):
        """
        Make sure that database names are escaped correctly
        """
        sub_domain = 'really.really.really.really.long.subdomain'
        base_domain = 'this-is-a-really-unusual-domain-แปลกมาก.com'
        internal_lms_domain = '{}.{}'.format(sub_domain, base_domain)
        self.instance = OpenEdXInstanceFactory(internal_lms_domain=internal_lms_domain)
        self.instance.provision_mysql()
        self.check_mysql()

    def test_provision_mysql_again(self):
        """
        Only create the database once
        """
        self.instance = OpenEdXInstanceFactory()
        self.instance.provision_mysql()
        self.assertIs(self.instance.mysql_provisioned, True)

        mysql_user = self.instance.mysql_user
        mysql_pass = self.instance.mysql_pass
        self.instance.provision_mysql()
        self.assertEqual(self.instance.mysql_user, mysql_user)
        self.assertEqual(self.instance.mysql_pass, mysql_pass)
        self.check_mysql()

    def test_provision_mysql_no_mysql_server(self):
        """
        Don't provision a mysql database if instance has no MySQL server
        """
        self.instance = OpenEdXInstanceFactory()
        self.instance.mysql_server = None
        self.instance.save()
        self.instance.provision_mysql()
        databases = subprocess.check_output("mysql -h 127.0.0.1 -u root -e 'SHOW DATABASES'", shell=True).decode()
        for database in self.instance.mysql_databases:
            self.assertNotIn(database["name"], databases)

    @patch_services
    @override_settings(DEFAULT_INSTANCE_MYSQL_URL='mysql://user:pass@mysql.opencraft.com')
    def test_ansible_settings_mysql(self, mocks):
        """
        Test that get_database_settings produces correct settings for MySQL databases
        """
        # Delete MySQLServer object created during the migrations to allow the settings override to
        # take effect.
        MySQLServer.objects.all().delete()
        self.instance = OpenEdXInstanceFactory()
        expected_host = "mysql.opencraft.com"
        expected_port = MYSQL_SERVER_DEFAULT_PORT

        def make_flat_group_info(var_names=None, database=None, include_port=True):
            """ Return dict containing info for a flat group of variables """
            group_info = {}
            if var_names:
                group_info["vars"] = var_names
            # Compute and insert values
            name = self.instance._get_mysql_database_name(database["name"])
            user = self.instance._get_mysql_user_name(database["user"])
            password = self.instance._get_mysql_pass(user)
            values = [name, user, password, expected_host]
            if include_port:
                values.append(expected_port)
            group_info["values"] = values
            return group_info

        def make_nested_group_info(var_names, databases):
            """ Return dict containing info for a nested group of variables """
            group_info = {
                "vars": var_names
            }
            # Compute and insert values
            for database in databases:
                database["name"] = self.instance._get_mysql_database_name(database["name"])
                database["user"] = self.instance._get_mysql_user_name(database["user"])
                database["password"] = self.instance._get_mysql_pass(database["user"])
            values = [database["name"] for database in databases]
            values.append({
                database.get("id", "default"): dict(
                    ENGINE='django.db.backends.mysql',
                    NAME=database["name"],
                    USER=database["user"],
                    PASSWORD=database["password"],
                    HOST=expected_host,
                    PORT=expected_port,
                    **database.get("additional_settings", {}),
                )
                for database in databases
            })
            group_info["values"] = values
            return group_info

        # Load instance settings
        db_vars = yaml.load(self.instance.get_database_settings())

        # Check instance settings for common users
        self.check_common_users(self.instance, db_vars)

        # Check service-specific instance settings
        var_groups = {
            "EDXAPP_MYSQL_": make_flat_group_info(database={"name": "edxapp", "user": "edxapp"}),
            "XQUEUE_MYSQL_": make_flat_group_info(database={"name": "xqueue", "user": "xqueue"}),
            "EDXAPP_MYSQL_CSMH_": make_flat_group_info(database={"name": "edxapp_csmh", "user": "edxapp"}),
            "NOTIFIER_DATABASE_": make_flat_group_info(
                var_names=["NAME", "USER", "PASSWORD", "HOST", "PORT"],
                database={"name": "notifier", "user": "notifier"}
            ),
            "EDX_NOTES_API_MYSQL_": make_flat_group_info(
                var_names=["DB_NAME", "DB_USER", "DB_PASS", "HOST"],
                database={"name": "edx_notes_api", "user": "notes"},
                include_port=False
            ),
            "ECOMMERCE_": {
                "vars": ["DATABASES"],
                "values": [{
                    "default": {
                        "ENGINE": 'django.db.backends.mysql',
                        "NAME": "{{ ECOMMERCE_DATABASE_NAME }}",
                        "USER": "{{ ECOMMERCE_DATABASE_USER }}",
                        "PASSWORD": "{{ ECOMMERCE_DATABASE_PASSWORD }}",
                        "HOST": "{{ ECOMMERCE_DATABASE_HOST }}",
                        "PORT": expected_port,
                        "ATOMIC_REQUESTS": True,
                        "CONN_MAX_AGE": 0
                    }
                }]
            },
            "ECOMMERCE_DATABASE_": make_flat_group_info(
                var_names=["NAME", "USER", "PASSWORD", "HOST"],
                database={"name": "ecommerce", "user": "ecommerce"}
            ),
            "PROGRAMS_": make_nested_group_info(
                ["DEFAULT_DB_NAME", "DATABASES"],
                [{"name": "programs", "user": "program", "additional_settings": {
                    "ATOMIC_REQUESTS": True,
                    "CONN_MAX_AGE": 0,
                }}]
            ),
            "INSIGHTS_": make_nested_group_info(
                ["DATABASE_NAME", "DATABASES"],
                [{"name": "dashboard", "user": "dashboard"}]
            ),
            "ANALYTICS_API_": make_nested_group_info(
                ["DEFAULT_DB_NAME", "REPORTS_DB_NAME", "DATABASES"],
                [{"name": "analytics_api", "user": "api"}, {"id": "reports", "name": "reports", "user": "reports"}]
            ),
        }
        for group_prefix, group_info in var_groups.items():
            values = group_info["values"]
            if "vars" in group_info:
                self.check_vars(self.instance, db_vars, group_prefix, var_names=group_info["vars"], values=values)
            else:
                self.check_vars(self.instance, db_vars, group_prefix, values=values)

    def test_ansible_settings_no_mysql_server(self):
        """
        Don't add mysql ansible vars if instance has no MySQL server
        """
        self.instance = OpenEdXInstanceFactory()
        self.instance.mysql_server = None
        self.instance.save()
        self.check_mysql_vars_not_set(self.instance)


@ddt.ddt
class MongoDBInstanceTestCase(TestCase):
    """
    Test cases for MongoDBInstanceMixin and OpenEdXDatabaseMixin
    """
    def setUp(self):
        super().setUp()
        self.instance = None

    def tearDown(self):
        if self.instance:
            self.instance.deprovision_mongo()
        super().tearDown()

    def check_mongo(self):
        """
        Check that the instance mongo user has access to the external mongo database
        """
        mongo = pymongo.MongoClient(settings.DEFAULT_INSTANCE_MONGO_URL)
        for database in self.instance.mongo_database_names:
            self.assertTrue(mongo[database].authenticate(self.instance.mongo_user, self.instance.mongo_pass))

    def check_mongo_vars_not_set(self, appserver):
        """
        Check that the given OpenEdXAppServer does not point to a mongo database
        """
        for var in ('EDXAPP_MONGO_USER',
                    'EDXAPP_MONGO_PASSWORD'
                    'EDXAPP_MONGO_HOSTS',
                    'EDXAPP_MONGO_PORT',
                    'EDXAPP_MONGO_DB_NAME',
                    'FORUM_MONGO_USER',
                    'FORUM_MONGO_PASSWORD',
                    'FORUM_MONGO_HOSTS',
                    'FORUM_MONGO_PORT',
                    'FORUM_MONGO_DATABASE'):
            self.assertNotIn(var, appserver.configuration_settings)

    def check_mongo_vars_set(self, appserver, expected_hosts, expected_replica_set=None):
        """
        Check that the given OpenEdXAppServer is using the expected mongo settings.
        """
        ansible_vars = appserver.configuration_settings
        self.assertIn('EDXAPP_MONGO_USER: {0}'.format(self.instance.mongo_user), ansible_vars)
        self.assertIn('EDXAPP_MONGO_PASSWORD: {0}'.format(self.instance.mongo_pass), ansible_vars)
        self.assertIn('EDXAPP_MONGO_PORT: {0}'.format(MONGODB_SERVER_DEFAULT_PORT), ansible_vars)
        self.assertIn('EDXAPP_MONGO_DB_NAME: {0}'.format(self.instance.mongo_database_name), ansible_vars)
        # Use regex match, because sometimes the mongo hosts are unordered
        self.assertRegex(ansible_vars, r"EDXAPP_MONGO_HOSTS:\s*{0}\n".format(expected_hosts))
        if expected_replica_set:
            self.assertIn('EDXAPP_MONGO_REPLICA_SET: {0}'.format(expected_replica_set), ansible_vars)
        else:
            self.assertNotIn('EDXAPP_MONGO_REPLICA_SET', ansible_vars)

        self.assertIn('FORUM_MONGO_USER: {0}'.format(self.instance.mongo_user), ansible_vars)
        self.assertIn('FORUM_MONGO_PASSWORD: {0}'.format(self.instance.mongo_pass), ansible_vars)
        self.assertIn('FORUM_MONGO_PORT: {0}'.format(MONGODB_SERVER_DEFAULT_PORT), ansible_vars)
        self.assertIn('FORUM_MONGO_DATABASE: {0}'.format(self.instance.forum_database_name), ansible_vars)

    def test_provision_mongo(self):
        """
        Provision mongo databases
        """
        self.instance = OpenEdXInstanceFactory()
        self.instance.provision_mongo()
        self.check_mongo()

    def test_provision_mongo_again(self):
        """
        Only create the databases once
        """
        self.instance = OpenEdXInstanceFactory()
        self.instance.provision_mongo()
        self.assertIs(self.instance.mongo_provisioned, True)

        mongo_user = self.instance.mongo_user
        mongo_pass = self.instance.mongo_pass
        self.instance.provision_mongo()
        self.assertEqual(self.instance.mongo_user, mongo_user)
        self.assertEqual(self.instance.mongo_pass, mongo_pass)
        self.check_mongo()

    def test_provision_mongo_no_mongodb_server(self):
        """
        Don't provision a mongo database if instance has no MongoDB server
        """
        mongo = pymongo.MongoClient(settings.DEFAULT_INSTANCE_MONGO_URL)
        self.instance = OpenEdXInstanceFactory()
        self.instance.mongodb_server = None
        self.instance.save()
        self.instance.provision_mongo()
        databases = mongo.database_names()
        for database in self.instance.mongo_database_names:
            self.assertNotIn(database, databases)

    @override_settings(DEFAULT_INSTANCE_MONGO_URL='mongodb://user:pass@mongo.opencraft.com')
    def test_ansible_settings_mongo(self):
        """
        Add mongo ansible vars if instance has a MongoDB server
        """
        # Delete MongoDBServer object created during the migrations to allow the settings override
        # to take effect.
        MongoDBServer.objects.all().delete()
        self.instance = OpenEdXInstanceFactory()
        appserver = make_test_appserver(self.instance)
        self.check_mongo_vars_set(appserver, expected_hosts='mongo.opencraft.com')

    @override_settings(
        DEFAULT_INSTANCE_MONGO_URL=None,
        DEFAULT_MONGO_REPLICA_SET_NAME="test_name",
        DEFAULT_MONGO_REPLICA_SET_USER="test",
        DEFAULT_MONGO_REPLICA_SET_PASSWORD="test",
        DEFAULT_MONGO_REPLICA_SET_PRIMARY="test.opencraft.hosting",
        DEFAULT_MONGO_REPLICA_SET_HOSTS="test.opencraft.hosting,test1.opencraft.hosting,test2.opencraft.hosting"
    )
    @ddt.data(
        ('open-release/ficus', 'open-release/ficus'),
        ('open-release/ficus', 'opencraft-release/ficus'),
        ('open-release/ginkgo', 'open-release/ginkgo'),
    )
    @ddt.unpack
    def test_ansible_settings_no_replica_set(self, openedx_release, configuration_version):
        """
        Prior to Hawthorn, edx configuration does not support MongoDB replica sets,
        and the mongo hosts must be a single host, provided as a list of strings.
        """
        # Delete MongoDBServer object created during the migrations to allow the settings override
        # to take effect.
        MongoDBServer.objects.all().delete()
        self.instance = OpenEdXInstanceFactory(openedx_release=openedx_release,
                                               configuration_version=configuration_version)
        appserver = make_test_appserver(self.instance)
        self.check_mongo_vars_set(appserver, expected_hosts="\n- test.opencraft.hosting")

    @override_settings(
        DEFAULT_INSTANCE_MONGO_URL=None,
        DEFAULT_MONGO_REPLICA_SET_NAME="test_name",
        DEFAULT_MONGO_REPLICA_SET_USER="test",
        DEFAULT_MONGO_REPLICA_SET_PASSWORD="test",
        DEFAULT_MONGO_REPLICA_SET_PRIMARY="test.opencraft.hosting",
        DEFAULT_MONGO_REPLICA_SET_HOSTS="test.opencraft.hosting,test1.opencraft.hosting,test2.opencraft.hosting"
    )
    @ddt.data(
        ('open-release/ginkgo', 'opencraft-release/ginkgo'),
        (settings.OPENEDX_RELEASE_STABLE_REF, settings.STABLE_CONFIGURATION_VERSION),
        (settings.DEFAULT_OPENEDX_RELEASE, settings.DEFAULT_CONFIGURATION_VERSION),
    )
    @ddt.unpack
    def test_ansible_settings_use_replica_set(self, openedx_release, configuration_version):
        """
        Add mongo ansible vars if instance has a MongoDB replica set
        Also, the mongo hosts are provied as a comma-separated string.
        """
        # Delete MongoDBServer object created during the migrations to allow the settings override
        # to take effect.
        MongoDBServer.objects.all().delete()
        self.instance = OpenEdXInstanceFactory(openedx_release=openedx_release,
                                               configuration_version=configuration_version)
        appserver = make_test_appserver(self.instance)
        self.check_mongo_vars_set(appserver,
                                  expected_hosts=r'test\d?.opencraft.hosting,'
                                                 r'test\d?.opencraft.hosting,'
                                                 r'test\d?.opencraft.hosting',
                                  expected_replica_set='test_name')

    def test_ansible_settings_no_mongo_server(self):
        """
        Don't add mongo ansible vars if instance has no MongoDB server
        """
        self.instance = OpenEdXInstanceFactory()
        self.instance.mongodb_server = None
        self.instance.save()
        appserver = make_test_appserver(self.instance)
        self.check_mongo_vars_not_set(appserver)

    @override_settings(
        DEFAULT_INSTANCE_MONGO_URL=None,
        DEFAULT_MONGO_REPLICA_SET_NAME="test_name",
        DEFAULT_MONGO_REPLICA_SET_USER="test",
        DEFAULT_MONGO_REPLICA_SET_PASSWORD="test",
        DEFAULT_MONGO_REPLICA_SET_PRIMARY="test.opencraft.hosting",
        DEFAULT_MONGO_REPLICA_SET_HOSTS="test.opencraft.hosting,test1.opencraft.hosting,test2.opencraft.hosting"
    )
    def test__get_main_database_url(self):
        """
        Main database url should be extracted from primary replica set MongoDBServer
        """
        self.instance = OpenEdXInstanceFactory()
        self.assertEqual(
            self.instance._get_main_database_url(),
            "mongodb://test:test@test.opencraft.hosting"
        )


@ddt.ddt
class RabbitMQInstanceTestCase(TestCase):
    """
    Test cases for RabbitMQInstanceMixin
    """
    def setUp(self):
        super().setUp()
        self.instance = OpenEdXInstanceFactory()

    @responses.activate
    @ddt.data(
        ('GET', ['overview'], '/api/overview'),
        ('PUT', ['users', 'testuser'], '/api/users/testuser'),
        ('DELETE', ['permissions', '/some_vhost', 'testuser'], '/api/permissions/%2Fsome_vhost/testuser')
    )
    @ddt.unpack
    def test_rabbitmq_request(self, method, url_parts, expected_url):
        """
        Test to make sure the _rabbitmq_request parameters form the correct URLs
        """
        url = '{service_url}{path}'.format(
            service_url=self.instance.rabbitmq_server.api_url,
            path=expected_url
        )
        expected_body = {'info': 'This is a mocked request to URL {url}'.format(url=url)}

        # Mock the URL with a uniquely identifying body so that we can verify that the
        # correct URL is formed and called.
        responses.add(method, url, json=expected_body)
        self.instance = OpenEdXInstanceFactory()
        response = self.instance._rabbitmq_request(method.lower(), *url_parts)

        self.assertDictEqual(
            response.json(),
            expected_body
        )

    @responses.activate
    def test_provision_rabbitmq(self):
        """
        Record the calls to the RabbitMQ API and make sure a new vhost along with
        two new users are created during provision and deleted during deprobision.

        The use of `responses.RequestsMock` raises an exception during context deconstruction
        if any of the URLs added to the `responses` object aren't ever called. Also,
        if any RabbitMQ API URLs are called that haven't been mocked, a `RabbitMQAPIError`
        should be raised (given the default `.env.test` configuration).

        So, this test should pass if and only if all of the specifically mocked URLs are
        called during both provision and deprovision.
        """
        rabbitmq_users = [self.instance.rabbitmq_provider_user, self.instance.rabbitmq_consumer_user]
        rabbitmq_vhost = urllib.parse.quote(self.instance.rabbitmq_vhost, safe='')

        vhosts_calls = ['vhosts/{}'.format(rabbitmq_vhost)]
        users_calls = ['users/{}'.format(user) for user in rabbitmq_users]
        permissions_calls = ['permissions/{}/{}'.format(rabbitmq_vhost, user) for user in rabbitmq_users]

        provision_calls = [
            '{}/api/{}'.format(self.instance.rabbitmq_server.api_url, url)
            for url in vhosts_calls + users_calls + permissions_calls
        ]
        deprovision_calls = [
            '{}/api/{}'.format(self.instance.rabbitmq_server.api_url, url)
            for url in vhosts_calls + users_calls
        ]

        # Spec the provisioning calls
        with responses.RequestsMock() as rsps:
            for url in provision_calls:
                rsps.add(
                    responses.PUT,
                    url,
                    content_type='application/json',
                    body='{}'
                )
            self.instance.provision_rabbitmq()

        # Spec the deprovisioning calls
        with responses.RequestsMock() as rsps:
            for url in deprovision_calls:
                rsps.add(
                    responses.DELETE,
                    url,
                    content_type='application/json',
                    body='{}'
                )
            self.instance.deprovision_rabbitmq()

    @responses.activate
    def test_rabbitmq_api_error(self):
        """
        Test that RabbitMQAPIError is thrown during auth issues
        """
        with responses.RequestsMock() as rsps:
            # Emulate 401 Unauthorized
            rsps.add(
                responses.GET,
                '{}/api/overview'.format(self.instance.rabbitmq_server.api_url),
                content_type='application/json',
                body='{}',
                status=401
            )
            with self.assertRaises(RabbitMQAPIError):
                self.instance._rabbitmq_request('get', 'overview')

    @ddt.data(
        ({'name': 'test'}, 'test'),
        ({'name': 'test', 'description': 'test description'}, 'test (test description)')
    )
    @ddt.unpack
    def test_string_representation(self, fields, representation):
        """
        Test that the str method returns the appropriate values.
        """
        rabbitmq = self.instance.rabbitmq_server
        for name, value in fields.items():
            setattr(rabbitmq, name, value)
        rabbitmq.save()
        self.assertEqual(str(rabbitmq), representation)


class RabbitMQServerManagerTestCase(TestCase):
    """
    Tests for RabbitMQServerManager.
    """
    @override_settings(DEFAULT_RABBITMQ_API_URL=None)
    def test_no_rabbitmq_server_available(self):
        """
        Test that get_random() raises an exception when no rabbitmq servers are available.
        """
        RabbitMQServer.objects.all().delete()
        with self.assertRaises(RabbitMQServer.DoesNotExist):
            RabbitMQServer.objects.select_random()

    @override_settings(DEFAULT_RABBITMQ_API_URL="http://doesnotexist.example.com:12345")
    def test_invalid_rabbitmq_server(self):
        """
        Verify that an exception gets raised when the credentials are missing from from the
        setting for the default rabbitmq API url server.
        """
        with self.assertRaises(ImproperlyConfigured):
            RabbitMQServer.objects.select_random()

    @patch('instance.models.rabbitmq_server.logger')
    def test_mismatch_warning(self, mock_logger):  # pylint: disable=no-self-use
        """
        Test that a warning is logged when trying to spawn the default, but a default already
        and contains mismatching parameters with the given settings.
        """
        urls = ['http://user:pass@doesnotexist.example.com:12345', 'http://user2:pass2@doesnotexist.example.com:12345']
        for url in urls:
            with override_settings(DEFAULT_RABBITMQ_API_URL=url):
                RabbitMQServer.objects._create_default()
        mock_logger.warning.assert_called_with(
            'RabbitMQServer for %s already exists, and its settings do not match the Django '
            'settings: %s vs %s, %s vs %s, %s vs %s, %s vs %s, %s vs %s, %s vs %s',
            'accepts_new_clients', True,
            'admin_password', 'pass2',
            'admin_username', 'user2',
            'api_url', 'http://doesnotexist.example.com:12345',
            'instance_host', 'rabbitmq.example.com',
            'instance_port', 5671,
        )
