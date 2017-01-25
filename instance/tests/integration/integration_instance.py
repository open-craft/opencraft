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
Instance - Integration Tests
"""
# Imports #####################################################################

import os
from unittest.mock import patch
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils.six import StringIO
import MySQLdb as mysql
import pymongo

from instance.models.appserver import Status as AppServerStatus
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.server import Status as ServerStatus
from instance.openstack_utils import stat_container
from instance.tests.decorators import patch_git_checkout
from instance.tests.integration.base import IntegrationTestCase
from instance.tests.integration.factories.instance import OpenEdXInstanceFactory
from instance.tests.integration.utils import check_url_accessible, is_port_open
from instance.tasks import spawn_appserver
from opencraft.tests.utils import shard
from registration.models import BetaTestApplication


# Tests #######################################################################

class InstanceIntegrationTestCase(IntegrationTestCase):
    """
    Integration test cases for instance high-level tasks
    """
    EXPECTED_SECRET_KEYS = (
        'ANALYTICS_API_SECRET_KEY',
        'EDXAPP_EDXAPP_SECRET_KEY',
        'FORUM_API_KEY',
    )

    def assert_instance_up(self, instance):
        """
        Check that the given instance is up and accepting requests
        """
        instance.refresh_from_db()
        self.assertIsNotNone(instance.active_appserver)
        self.assertEqual(instance.active_appserver.status, AppServerStatus.Running)
        self.assertEqual(instance.active_appserver.server.status, ServerStatus.Ready)
        server = instance.active_appserver.server
        check_url_accessible('http://{0}/'.format(server.public_ip))
        for url in [instance.url, instance.lms_preview_url, instance.studio_url]:
            check_url_accessible(url)

    def assert_appserver_firewalled(self, instance):
        """
        Ensure the instance's appserver is not exposing any services it shouldn't be
        """
        instance.refresh_from_db()
        self.assertIsNotNone(instance.active_appserver)
        server_ip = instance.active_appserver.server.public_ip
        ports_should_be_open = [22, 80]  # 443 may or may not be open, depending on instance.protocol
        for port in ports_should_be_open:
            self.assertTrue(
                is_port_open(server_ip, port),
                "Expected port {} on AppServer VM {} to be open.".format(port, server_ip)
            )
        ports_should_be_inaccessible = [
            3306,  # MySQL
            8000,  # LMS (direct)
            8001,  # Studio (direct)
            8002,  # ecommerce
            9200,  # ElasticSearch
            11211,  # memcached
            18080,  # Forums Service
            27017,  # MongoDB
        ]
        for port in ports_should_be_inaccessible:
            self.assertFalse(
                is_port_open(server_ip, port),
                "Expected port {} on AppServer VM {} to be open.".format(port, server_ip)
            )

    def assert_swift_container_provisioned(self, instance):
        """
        Verify the Swift container for the instance has been provisioned successfully.
        """
        if not settings.SWIFT_ENABLE:
            return

        stat_result = stat_container(instance.swift_container_name)
        self.assertEqual(stat_result.read_acl, '.r:*')

    def assert_secret_keys(self, instance, appserver):
        """
        Verify that the appserver's configuration includes expected secret keys.
        """
        for expected_key in self.EXPECTED_SECRET_KEYS:
            self.assertIn(instance.get_secret_key_for_var(expected_key), appserver.configuration_settings)

    def assert_mysql_db_provisioned(self, instance):
        """
        Verify that the MySQL database for the instance has been provisioned and can be
        connected to with the credentials the instance provides.
        """
        mysql_url_obj = urlparse(settings.DEFAULT_INSTANCE_MYSQL_URL)
        for database in instance.mysql_databases:
            connection = mysql.connect(
                host=mysql_url_obj.hostname,
                user=database['user'],
                passwd=instance._get_mysql_pass(database['user']),
                port=mysql_url_obj.port or 3306,
            )
            database_name = connection.escape_string(database['name']).decode()
            cur = connection.cursor()
            result = cur.execute(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                (database_name,),
            )
            self.assertEqual(result, 1)

    def assert_mongo_db_provisioned(self, instance):
        """
        Verify that the databases ostensibly created by the provisioning process actually were.
        """
        mongo_url_obj = urlparse(settings.DEFAULT_INSTANCE_MONGO_URL)
        for db_name in instance.mongo_database_names:
            mongo = pymongo.MongoClient(
                host=mongo_url_obj.hostname,
                port=mongo_url_obj.port or 27017
            )
            # Verify that we can log into a particular database, using the instance's saved
            # mongo username and password
            db = getattr(mongo, db_name)
            # Successful authentication will return True; failure will raise an exception.
            result = db.authenticate(
                name=instance.mongo_user,
                password=instance.mongo_pass,
            )
            self.assertTrue(result)
            db.logout()

    @shard(1)
    def test_spawn_appserver(self):
        """
        Provision an instance and spawn an AppServer
        """
        OpenEdXInstanceFactory(name='Integration - test_spawn_appserver')
        instance = OpenEdXInstance.objects.get()
        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=2)
        self.assert_instance_up(instance)
        self.assert_appserver_firewalled(instance)
        self.assertTrue(instance.successfully_provisioned)
        self.assertTrue(instance.require_user_creation_success())
        for appserver in instance.appserver_set.all():
            self.assert_secret_keys(instance, appserver)

    @shard(2)
    def test_external_databases(self):
        """
        Ensure that the instance can connect to external databases
        """
        if not settings.DEFAULT_INSTANCE_MYSQL_URL or not settings.DEFAULT_INSTANCE_MONGO_URL:
            print('External databases not configured, skipping integration test')
            return
        OpenEdXInstanceFactory(name='Integration - test_external_databases', use_ephemeral_databases=False)
        instance = OpenEdXInstance.objects.get()
        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=2)
        self.assert_swift_container_provisioned(instance)
        self.assert_instance_up(instance)
        self.assert_appserver_firewalled(instance)
        self.assertTrue(instance.successfully_provisioned)
        self.assertFalse(instance.require_user_creation_success())
        for appserver in instance.appserver_set.all():
            self.assert_secret_keys(instance, appserver)
        self.assert_mysql_db_provisioned(instance)
        self.assert_mongo_db_provisioned(instance)

    @shard(3)
    def test_activity_csv(self):
        """
        Run the activity_csv management command against a live instance.
        """
        OpenEdXInstanceFactory(name='Integration - test_spawn_appserver')
        instance = OpenEdXInstance.objects.get()
        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=2)
        self.assert_instance_up(instance)
        self.assertTrue(instance.successfully_provisioned)
        self.assertTrue(instance.require_user_creation_success())

        user = User.objects.create_user('betatestuser', 'betatest@example.com')

        BetaTestApplication.objects.create(
            user=user,
            subdomain='betatestdomain',
            instance_name='betatestinstance',
            public_contact_email='publicemail@example.com',
            project_description='I want to beta test OpenCraft IM',
            status=BetaTestApplication.ACCEPTED,
            instance=instance,
        )

        # Run the management command and collect the CSV from stdout.
        out = StringIO()
        call_command('activity_csv', stdout=out)

        out_lines = out.getvalue().split('\r\n')

        # The output should look similar to this when one instance is launched:
        #
        #   "Appserver IP","Internal LMS Domain","Name","Contact Email","Unique Hits","Total Users","Total Courses",
        #     "Age (Days)"
        #   "213.32.77.49","test.example.com","Instance","betatest@example.com","87","6","1",1

        self.assertEqual(
            '"Appserver IP","Internal LMS Domain","Name","Contact Email","Unique Hits","Total Users","Total Courses",'
            '"Age (Days)"',
            out_lines[0]
        )
        self.assertIn('"Integration - test_spawn_appserver"', out_lines[1])
        self.assertIn('"betatest@example.com"', out_lines[1])
        self.assertNotIn('N/A', out_lines[1])

        # stdout should contain 3 lines (as opposed to 2) to account for the last newline.
        self.assertEqual(len(out_lines), 3)

    @patch_git_checkout
    def test_ansible_failure(self, git_checkout, git_working_dir):
        """
        Ensure failures in the ansible flow are reflected in the instance
        """
        git_working_dir.return_value = os.path.join(os.path.dirname(__file__), "ansible")

        instance = OpenEdXInstanceFactory(name='Integration - test_ansible_failure')
        with patch.object(OpenEdXAppServer, 'CONFIGURATION_PLAYBOOK', new="playbooks/failure.yml"):
            spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=1)
        instance.refresh_from_db()
        self.assertIsNone(instance.active_appserver)
        appserver = instance.appserver_set.last()
        self.assertEqual(appserver.status, AppServerStatus.ConfigurationFailed)
        self.assertEqual(appserver.server.status, ServerStatus.Ready)

    @patch_git_checkout
    def test_ansible_failignore(self, git_checkout, git_working_dir):
        """
        Ensure failures that are ignored aren't reflected in the instance
        """
        git_working_dir.return_value = os.path.join(os.path.dirname(__file__), "ansible")

        instance = OpenEdXInstanceFactory(name='Integration - test_ansible_failignore')
        with patch.object(OpenEdXAppServer, 'CONFIGURATION_PLAYBOOK', new="playbooks/failignore.yml"):
            spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=1)
        instance.refresh_from_db()
        self.assertIsNotNone(instance.active_appserver)
        self.assertEqual(instance.active_appserver.status, AppServerStatus.Running)
        self.assertEqual(instance.active_appserver.server.status, ServerStatus.Ready)
