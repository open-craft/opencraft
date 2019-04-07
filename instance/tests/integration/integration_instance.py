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
Instance - Integration Tests
"""
# Imports #####################################################################

import os
import re
import time
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import override_settings
from django.utils.six import StringIO
import MySQLdb as mysql
import pymongo

from instance.models.appserver import AppServer, Status as AppServerStatus
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.server import OpenStackServer, Status as ServerStatus
from instance.openstack_utils import stat_container
from instance.tests.decorators import patch_git_checkout
from instance.tests.integration.base import IntegrationTestCase
from instance.tests.integration.factories.instance import OpenEdXInstanceFactory
from instance.tests.integration.utils import check_url_accessible, get_url_contents, is_port_open
from instance.tasks import spawn_appserver
from opencraft.tests.utils import shard
from registration.approval import on_appserver_spawned
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
        auth = (instance.http_auth_user, instance.http_auth_pass)
        active_appservers = list(instance.get_active_appservers().all())
        self.assertEqual(len(active_appservers), 1)
        self.assertTrue(active_appservers[0].is_active)
        self.assertEqual(active_appservers[0].status, AppServerStatus.Running)
        self.assertEqual(active_appservers[0].server.status, ServerStatus.Ready)
        server = active_appservers[0].server
        check_url_accessible('http://{0}/'.format(server.public_ip), auth=auth)
        for url in [instance.url, instance.lms_preview_url, instance.studio_url]:
            check_url_accessible(url)

    def assert_appserver_firewalled(self, instance):
        """
        Ensure the instance's appserver is not exposing any services it shouldn't be
        """
        instance.refresh_from_db()
        active_appservers = list(instance.get_active_appservers().all())
        self.assertEqual(len(active_appservers), 1)
        server_ip = active_appservers[0].server.public_ip
        ports_should_be_open = [22, 80]
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
                "Expected port {} on AppServer VM {} to be inaccessible.".format(port, server_ip)
            )

    def assert_swift_container_provisioned(self, instance):
        """
        Verify the Swift container for the instance has been provisioned successfully.
        """
        if not instance.storage_type == instance.SWIFT_STORAGE:
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

    def assert_lms_users_provisioned(self, user, appserver):
        """
        Ensure the lms user playbook was run on the appserver.
        """
        self.assertEqual(appserver.lms_users.count(), 1)
        self.assertEqual(appserver.lms_users.get(), user)
        self.assertTrue(appserver.lms_user_settings)

        lms_user_playbook = appserver.lms_user_creation_playbook()
        self.assertTrue(lms_user_playbook)
        self.assertIn(lms_user_playbook, appserver.get_playbooks())

    def _assert_theme_colors_in_css(self, instance, application, css_url):
        """
        Check that the CSS in the server includes the colors requested in the application.
        E.g. after setting #3c9a12, we will find strings like this one in the minified CSS:
         .action-primary{box-shadow:0 2px 1px 0 #0a4a67;background:#3c9a12;color:#fff}
        """
        server_css = get_url_contents(instance.url + css_url)

        self.assertIn(application.main_color, server_css)
        self.assertIn(application.link_color, server_css)
        self.assertIn(application.header_bg_color, server_css)
        self.assertIn(application.footer_bg_color, server_css)

    def _assert_theme_logo_in_html(self, instance, application, logo_url):
        """
        Check whether the logo has the same size (in bytes) as the one from the beta registration form.
        Could be improved to a hash check, or to test equality of the binary contents.
        """
        orig_logo_size = len(get_url_contents(application.logo.url, verify_ssl=False))
        seen_logo_size = len(get_url_contents(instance.url + logo_url))
        self.assertEqual(orig_logo_size, seen_logo_size)

    def _assert_theme_favicon_in_html(self, instance, application, favicon_url):
        """
        Check whether favicon has the same size. Same system as with the logo.
        """
        orig_favicon_size = len(get_url_contents(application.favicon.url, verify_ssl=False))
        seen_favicon_size = len(get_url_contents(instance.url + favicon_url))
        self.assertEqual(orig_favicon_size, seen_favicon_size)

    def assert_theme_provisioned(self, instance, appserver, application):
        """
        Ensure the theme settings requested through the registration form resulted in
        a new theme being created which includes the specified colors and logo/favicon.
        This test check that simpletheme was set up correctly.
        """
        self.assertTrue('SIMPLETHEME_ENABLE_DEPLOY: true' in appserver.configuration_settings)

        # Connect to the appserver and check that simple_theme is enabled
        # Authentication not required
        server_html = get_url_contents(instance.url)
        self.assertIn('<link href="/static/simple-theme/css/lms-main', server_html)

        # Check that a CSS file under the right URL exists
        # The HTML contains a line like:
        #     <link href="/static/simple-theme/css/lms-main-v1.f6b41d8970dc.css" rel="stylesheet" type="text/css" />
        # and we need just the href
        css_extractor = re.search(r'<link href="(/static/simple-theme/css/lms-main-v1\.[a-z0-9]{12}\.css)" '
                                  r'rel="stylesheet" type="text/css" />',
                                  server_html)
        self.assertTrue(css_extractor)
        css_url = css_extractor.group(1)

        self._assert_theme_colors_in_css(instance, application, css_url)

        # The logo is found in a line like this in the HTML:
        #       <img src="/static/simple-theme/images/logo.82fb8d18479f.png" alt="danieltest1b Home Page"/>
        logo_extractor = re.search(r'<img\s+class="logo"\s+src="(/static/simple-theme/images/logo.[a-z0-9]+\.png)"',
                                   server_html)
        self.assertTrue(logo_extractor)
        logo_url = logo_extractor.group(1)

        self._assert_theme_logo_in_html(instance, application, logo_url)

        # Favicon is in a line like
        # <link rel="icon" type="image/x-icon" href="/static/simple-theme/images/favicon.eb143b51964d.ico" />
        favicon_extractor = re.search(r'<link rel="icon" type="image/x-icon" '
                                      r'href="(/static/simple-theme/images/favicon\.[a-z0-9]+\.ico)" />',
                                      server_html)
        self.assertTrue(favicon_extractor)
        favicon_url = favicon_extractor.group(1)

        self._assert_theme_favicon_in_html(instance, application, favicon_url)

    def assert_bucket_configured(self, instance):
        """
        Ensure bucket is configured with proper lifecycle and versioning
        """
        # Make sure versioning is enabled
        response = instance.s3.get_bucket_versioning(Bucket=instance.s3_bucket_name)
        self.assertEqual(response.get('Status'), 'Enabled')

        # Make sure expiration lifecycle is enabled
        response = instance.s3.get_bucket_lifecycle_configuration(Bucket=instance.s3_bucket_name)
        self.assertIn('Rules', response)
        days = None
        for rule in response.get('Rules'):
            if rule.get('Status') == 'Enabled' and 'NoncurrentVersionExpiration' in rule:
                days = rule.get('NoncurrentVersionExpiration').get('NoncurrentDays')
                break
        self.assertEqual(settings.S3_VERSION_EXPIRATION, days)

    @override_settings(INSTANCE_STORAGE_TYPE='s3')
    @shard(1)
    def test_spawn_appserver(self):
        """
        Provision an instance and spawn an AppServer, complete with custom theme (colors)
        """
        OpenEdXInstanceFactory(
            name='Integration - test_spawn_appserver',
            deploy_simpletheme=True,
        )
        instance = OpenEdXInstance.objects.get()

        # Add an lms user, as happens with beta registration
        user, _ = get_user_model().objects.get_or_create(username='test', email='test@example.com')
        instance.lms_users.add(user)

        # Simulate that the application form was filled. This doesn't create another instance nor user
        application = BetaTestApplication.objects.create(
            user=user,
            subdomain='betatestdomain',
            instance_name=instance.name,
            public_contact_email='publicemail@example.com',
            project_description='I want to beta test OpenCraft IM',
            status=BetaTestApplication.PENDING,
            # The presence of these colors will be checked later
            # Note: avoid string like #ffbb66 because it would be shortened to #fb6 and therefore
            # much harder to detect ("#ffbb66" wouldn't appear in CSS). Use e.g. #ffbb67
            main_color='#13709b',
            link_color='#14719c',
            header_bg_color='#ffbb67',
            footer_bg_color='#ddff89',
            instance=instance,
        )

        # We don't want to simulate e-mail verification of the user who submitted the application,
        # because that would start provisioning. Instead, we provision ourselves here.

        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=2)

        self.assert_instance_up(instance)
        self.assert_bucket_configured(instance)
        self.assert_appserver_firewalled(instance)
        self.assertTrue(instance.successfully_provisioned)
        for appserver in instance.appserver_set.all():
            self.assert_secret_keys(instance, appserver)
            self.assert_lms_users_provisioned(user, appserver)
            self.assert_theme_provisioned(instance, appserver, application)

    @override_settings(INSTANCE_STORAGE_TYPE='s3')
    def test_betatest_accepted(self):
        """
        Provision an instance, spawn an AppServer and accepts the application.
        """
        OpenEdXInstanceFactory(
            name='Integration - test_betatest_accepted',
            deploy_simpletheme=True,
        )
        instance = OpenEdXInstance.objects.get()

        # Add an lms user, as happens with beta registration
        user, _ = get_user_model().objects.get_or_create(username='test', email='test@example.com')
        instance.lms_users.add(user)

        # Simulate that the application form was filled. This doesn't create another instance nor user
        BetaTestApplication.objects.create(
            user=user,
            subdomain='betatestdomain',
            instance_name=instance.name,
            public_contact_email='publicemail@example.com',
            project_description='I want to beta test OpenCraft IM',
            status=BetaTestApplication.PENDING,
            instance=instance,
        )

        appserver = MagicMock()
        appserver.status = AppServer.Status.Running
        instance.refresh_from_db()

        # Test accepting beta test application
        on_appserver_spawned(None, instance=instance, appserver=appserver)
        self.assertEqual(instance.betatestapplication_set.first().status, BetaTestApplication.ACCEPTED)

    @shard(2)
    @override_settings(INSTANCE_STORAGE_TYPE='s3')
    def test_external_databases(self):
        """
        Ensure that the instance can connect to external databases
        """
        if not settings.DEFAULT_INSTANCE_MYSQL_URL or not settings.DEFAULT_INSTANCE_MONGO_URL:
            print('External databases not configured, skipping integration test')
            return
        OpenEdXInstanceFactory(name='Integration - test_external_databases')
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
    @override_settings(INSTANCE_STORAGE_TYPE='s3')
    def test_activity_csv(self):
        """
        Run the activity_csv management command against a live instance.
        """
        OpenEdXInstanceFactory(name='Integration - test_activity_csv')
        instance = OpenEdXInstance.objects.get()
        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=2)
        self.assert_instance_up(instance)
        self.assertTrue(instance.successfully_provisioned)

        user = get_user_model().objects.create_user('betatestuser', 'betatest@example.com')

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
        self.assertIn('"Integration - test_activity_csv"', out_lines[1])
        self.assertIn('"betatest@example.com"', out_lines[1])
        self.assertNotIn('N/A', out_lines[1])

        # stdout should contain 3 lines (as opposed to 2) to account for the last newline.
        self.assertEqual(len(out_lines), 3)

    @shard(3)
    @patch_git_checkout
    @override_settings(INSTANCE_STORAGE_TYPE='s3')
    def test_ansible_failure(self, git_checkout, git_working_dir):
        """
        Ensure failures in the ansible flow are reflected in the instance
        """
        git_working_dir.return_value = os.path.join(os.path.dirname(__file__), "ansible")

        instance = OpenEdXInstanceFactory(
            name='Integration - test_ansible_failure',
            configuration_playbook_name='playbooks/failure.yml'
        )
        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=1)
        instance.refresh_from_db()
        self.assertFalse(instance.get_active_appservers().exists())
        appserver = instance.appserver_set.last()
        self.assertFalse(appserver.is_active)
        self.assertEqual(appserver.status, AppServerStatus.ConfigurationFailed)
        self.assertEqual(appserver.server.status, ServerStatus.Ready)

    @shard(1)
    @patch_git_checkout
    @patch("instance.models.openedx_appserver.OpenEdXAppServer.heartbeat_active")
    @override_settings(INSTANCE_STORAGE_TYPE='s3')
    def test_ansible_failignore(self, heartbeat_active, git_checkout, git_working_dir):
        """
        Ensure failures that are ignored aren't reflected in the instance
        """
        git_working_dir.return_value = os.path.join(os.path.dirname(__file__), "ansible")
        heartbeat_active.return_value = True
        instance = OpenEdXInstanceFactory(
            name='Integration - test_ansible_failignore',
            configuration_playbook_name='playbooks/failignore.yml'
        )
        with self.settings(ANSIBLE_APPSERVER_PLAYBOOK='playbooks/failignore.yml'):
            spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=1)
        instance.refresh_from_db()
        active_appservers = list(instance.get_active_appservers().all())
        self.assertEqual(len(active_appservers), 1)
        self.assertTrue(active_appservers[0].is_active)
        self.assertEqual(active_appservers[0].status, AppServerStatus.Running)
        self.assertEqual(active_appservers[0].server.status, ServerStatus.Ready)

    @shard(1)
    @override_settings(INSTANCE_STORAGE_TYPE='s3')
    def test_openstack_server_terminated(self):
        """
        Test that OpenStackServer detects if the VM was terminated externally.
        """
        server = OpenStackServer(name_prefix="integration_test")
        server.save()
        server.start()
        server.sleep_until(lambda: server.status.accepts_ssh_commands, timeout=120)
        server.os_server.delete()
        time.sleep(10)
        self.assertEqual(server.update_status(), ServerStatus.Terminated)
