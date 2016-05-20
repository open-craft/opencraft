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
OpenEdXInstance Database Mixins - Tests
"""

# Imports #####################################################################

import subprocess
from urllib.parse import urlparse

import pymongo
import yaml
from django.conf import settings
from django.test.utils import override_settings

from instance.tests.base import TestCase
from instance.tests.models.factories.openedx_appserver import make_test_appserver
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import patch_services


# Tests #######################################################################

#pylint: disable=no-member


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
            mysql_cmd = "mysql -u {user} -e 'SHOW TABLES' {db_name}".format(user=user, db_name=database_name)
            tables = subprocess.call(mysql_cmd, shell=True, env=env)
            self.assertEqual(tables, 0)

    def check_mysql(self):
        """
        Check that the mysql databases and users have been created
        """
        self.assertIs(self.instance.mysql_provisioned, True)
        self.assertTrue(self.instance.mysql_user)
        self.assertTrue(self.instance.mysql_pass)
        databases = subprocess.check_output("mysql -u root -e 'SHOW DATABASES'", shell=True).decode()
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

    def test_provision_mysql(self):
        """
        Provision mysql database
        """
        self.instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mysql()
        self.check_mysql()

    @override_settings(INSTANCE_MYSQL_URL_OBJ=None)
    def test_provision_mysql_no_url(self):
        """
        Don't provision a mysql database if INSTANCE_MYSQL_URL is not set
        """
        self.instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mysql()
        databases = subprocess.check_output("mysql -u root -e 'SHOW DATABASES'", shell=True).decode()
        for database in self.instance.mysql_databases:
            self.assertNotIn(database["name"], databases)

    def test_provision_mysql_weird_domain(self):
        """
        Make sure that database names are escaped correctly
        """
        sub_domain = 'really.really.really.really.long.subdomain'
        base_domain = 'this-is-a-really-long-unusual-domain-แปลกมาก.com'
        self.instance = OpenEdXInstanceFactory(use_ephemeral_databases=False,
                                               sub_domain=sub_domain,
                                               base_domain=base_domain)
        self.instance.provision_mysql()
        self.check_mysql()

    def test_provision_mysql_again(self):
        """
        Only create the database once
        """
        self.instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mysql()
        self.assertIs(self.instance.mysql_provisioned, True)

        mysql_user = self.instance.mysql_user
        mysql_pass = self.instance.mysql_pass
        self.instance.provision_mysql()
        self.assertEqual(self.instance.mysql_user, mysql_user)
        self.assertEqual(self.instance.mysql_pass, mysql_pass)
        self.check_mysql()

    @patch_services
    @override_settings(INSTANCE_MYSQL_URL_OBJ=urlparse('mysql://user:pass@mysql.opencraft.com'))
    def test_ansible_settings_mysql(self, mocks):
        """
        Add mysql ansible vars if INSTANCE_MYSQL_URL is set and not using ephemeral databases
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_mysql()

        db_vars = yaml.load(instance.get_database_settings())
        self.assertGreater(len(instance.mysql_user), 5)
        self.assertGreater(len(instance.mysql_pass), 10)
        self.assertEqual(db_vars['EDXAPP_MYSQL_USER'], instance.mysql_user)
        self.assertEqual(db_vars['EDXAPP_MYSQL_PASSWORD'], instance.mysql_pass)
        self.assertEqual(db_vars['EDXAPP_MYSQL_HOST'], 'mysql.opencraft.com')
        self.assertEqual(db_vars['EDXAPP_MYSQL_PORT'], 3306)
        self.assertEqual(db_vars['EDXAPP_MYSQL_DB_NAME'], instance.mysql_database_name)
        self.assertEqual(db_vars['COMMON_MYSQL_MIGRATE_USER'], instance.mysql_user)
        self.assertEqual(db_vars['COMMON_MYSQL_MIGRATE_PASS'], instance.mysql_pass)

    @patch_services
    @override_settings(INSTANCE_MYSQL_URL_OBJ=None)
    def test_ansible_settings_mysql_not_set(self, mocks):
        """
        Don't add mysql ansible vars if INSTANCE_MYSQL_URL is not set
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        instance.provision_mysql()
        self.check_mysql_vars_not_set(instance)

    @patch_services
    @override_settings(INSTANCE_MYSQL_URL_OBJ=urlparse('mysql://user:pass@mysql.opencraft.com'))
    def test_ansible_settings_mysql_ephemeral(self, mocks):
        """
        Don't add mysql ansible vars for ephemeral databases
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=True)
        instance.provision_mysql()
        self.check_mysql_vars_not_set(instance)


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
        mongo = pymongo.MongoClient(settings.INSTANCE_MONGO_URL)
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

    def test_provision_mongo(self):
        """
        Provision mongo databases
        """
        self.instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mongo()
        self.check_mongo()

    def test_provision_mongo_no_url(self):
        """
        Don't provision any mongo databases if INSTANCE_MONGO_URL is not set
        """
        mongo = pymongo.MongoClient(settings.INSTANCE_MONGO_URL)
        with override_settings(INSTANCE_MONGO_URL=None):
            self.instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
            self.instance.provision_mongo()
            databases = mongo.database_names()
            for database in self.instance.mongo_database_names:
                self.assertNotIn(database, databases)

    def test_provision_mongo_again(self):
        """
        Only create the databases once
        """
        self.instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        self.instance.provision_mongo()
        self.assertIs(self.instance.mongo_provisioned, True)

        mongo_user = self.instance.mongo_user
        mongo_pass = self.instance.mongo_pass
        self.instance.provision_mongo()
        self.assertEqual(self.instance.mongo_user, mongo_user)
        self.assertEqual(self.instance.mongo_pass, mongo_pass)
        self.check_mongo()

    @override_settings(INSTANCE_MONGO_URL_OBJ=urlparse('mongodb://user:pass@mongo.opencraft.com'))
    def test_ansible_settings_mongo(self):
        """
        Add mongo ansible vars if INSTANCE_MONGO_URL is set
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=False)
        appserver = make_test_appserver(instance)
        ansible_vars = appserver.configuration_settings
        self.assertIn('EDXAPP_MONGO_USER: {0}'.format(instance.mongo_user), ansible_vars)
        self.assertIn('EDXAPP_MONGO_PASSWORD: {0}'.format(instance.mongo_pass), ansible_vars)
        self.assertIn('EDXAPP_MONGO_HOSTS: [mongo.opencraft.com]', ansible_vars)
        self.assertIn('EDXAPP_MONGO_PORT: 27017', ansible_vars)
        self.assertIn('EDXAPP_MONGO_DB_NAME: {0}'.format(instance.mongo_database_name), ansible_vars)
        self.assertIn('FORUM_MONGO_USER: {0}'.format(instance.mongo_user), ansible_vars)
        self.assertIn('FORUM_MONGO_PASSWORD: {0}'.format(instance.mongo_pass), ansible_vars)
        self.assertIn('FORUM_MONGO_HOSTS: [mongo.opencraft.com]', ansible_vars)
        self.assertIn('FORUM_MONGO_PORT: 27017', ansible_vars)
        self.assertIn('FORUM_MONGO_DATABASE: {0}'.format(instance.forum_database_name), ansible_vars)

    @override_settings(INSTANCE_MONGO_URL_OBJ=None)
    def test_ansible_settings_mongo_not_set(self):
        """
        Don't add mongo ansible vars if INSTANCE_MONGO_URL is not set
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=True)
        appserver = make_test_appserver(instance)
        self.check_mongo_vars_not_set(appserver)

    @override_settings(INSTANCE_MONGO_URL_OBJ=urlparse('mongodb://user:pass@mongo.opencraft.com'))
    def test_ansible_settings_mongo_ephemeral(self):
        """
        Don't add mongo ansible vars if INSTANCE_MONGO_URL is not set
        """
        instance = OpenEdXInstanceFactory(use_ephemeral_databases=True)
        appserver = make_test_appserver(instance)
        self.check_mongo_vars_not_set(appserver)
