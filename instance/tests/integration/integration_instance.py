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
from datetime import datetime
from functools import wraps
from unittest import skipIf
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils.six import StringIO
import MySQLdb as mysql
import pymongo

from instance.models.appserver import AppServer, Status as AppServerStatus
from instance.models.deployment import DeploymentType
from instance.models.mixins.ansible import Playbook
from instance.models.openedx_deployment import OpenEdXDeployment
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.server import OpenStackServer, Status as ServerStatus
from instance.tests.decorators import patch_git_checkout
from instance.tests.integration.base import IntegrationTestCase
from instance.tests.integration.factories.instance import OpenEdXInstanceFactory
from instance.tests.integration.utils import check_url_accessible, get_url_contents, is_port_open
from instance.tasks import spawn_appserver
from instance.utils import create_new_deployment
from registration.approval import on_appserver_spawned
from registration.models import BetaTestApplication
from userprofile.models import UserProfile


# TEST_GROUP should be an integer. This will skip any test that is not part of the group value.
# If it's None every integration test will run.
TEST_GROUP = os.getenv('TEST_GROUP')
print('TEST_GROUP: %s', (TEST_GROUP, ))
# Tests #######################################################################


def retry(f, exception=AssertionError, tries=5, delay=10):
    """
    Retry calling the decorated function
    """
    @wraps(f)
    def f_retry(*args, **kwargs):
        mtries, mdelay = tries, delay
        while mtries > 1:
            try:
                return f(*args, **kwargs)
            except exception:
                time.sleep(mdelay)
                mtries -= 1
        return f(*args, **kwargs)

    return f_retry  # true decorator


def spawn_openstack_server(name_prefix, retries=1):
    """
    Spawn an OpenStack server.

    :param name_prefix: Name prefix for OpenStack server
    :param retries: Number of times it retry spawn a server, defaults to 1
    :return: OpenStack server instance
    :raises: TimeoutError
    """
    while retries >= 0:
        server = OpenStackServer(name_prefix=name_prefix)
        server.save()
        server.start()

        try:
            server.sleep_until(lambda: server.status.accepts_ssh_commands, timeout=120)
        except TimeoutError as e:
            server.os_server.delete()
            retries -= 1
            if retries < 0:
                raise e
        else:
            return server


class InstanceIntegrationTestCase(IntegrationTestCase):
    """
    Integration test cases for instance high-level tasks
    """
    EXPECTED_SECRET_KEYS = (
        'ANALYTICS_API_SECRET_KEY',
        'EDXAPP_EDXAPP_SECRET_KEY',
        'FORUM_API_KEY',
    )

    @retry
    def assert_server_ready(self, instance):
        """
        Make sure the instance has an active, ready AppServer
        """
        instance.refresh_from_db()
        active_appservers = instance.get_active_appservers()
        self.assertEqual(active_appservers.count(), 1)
        appserver = active_appservers.first()
        self.assertTrue(appserver.is_active)
        self.assertEqual(appserver.status, AppServerStatus.Running)
        self.assertEqual(appserver.server.status, ServerStatus.Ready)

    @retry
    def assert_instance_up(self, instance):
        """
        Check that the given instance is up and accepting requests
        """
        auth = (instance.http_auth_user, instance.http_auth_pass)
        server = instance.get_active_appservers().first().server
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
        # <link rel="icon" type="image/x-icon" href="/static/simple-theme/images/favicon.eb143b51964d.ico"/>
        favicon_extractor = re.search(r'<link\s+rel="icon"\s+type="image/x-icon"'
                                      r'\s+href="(/static/simple-theme/images/favicon\.[a-z0-9]+\.ico)"'
                                      r'\s*/>',
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

    def assert_load_balanced_domains(self, instance):
        """
        Ensure instance has extra custom domains correctly configured.
        """
        expected_domain_names = [
            instance.external_lms_domain,
            instance.external_lms_preview_domain,
            instance.external_studio_domain,
            instance.external_discovery_domain,
            instance.external_ecommerce_domain,
            instance.external_mfe_domain,
            instance.internal_lms_domain,
            instance.internal_lms_preview_domain,
            instance.internal_studio_domain,
            instance.internal_discovery_domain,
            instance.internal_ecommerce_domain,
            instance.internal_mfe_domain,
            'custom1.{lms_domain}'.format(lms_domain=instance.internal_lms_domain),
            'custom2.{lms_domain}'.format(lms_domain=instance.internal_lms_domain),
        ]
        expected_domain_names = [domain for domain in expected_domain_names if domain]
        self.assertEqual(
            instance.get_load_balanced_domains(),
            expected_domain_names
        )

    def assert_static_content_overrides_work(self, instance, appserver, page):
        """
        Ensure that the static content overrides work.
        """
        self.assertTrue('EDXAPP_SITE_CONFIGURATION:' in appserver.configuration_settings)
        self.assertTrue('static_template_about_content' in appserver.configuration_settings)
        homepage_html = get_url_contents(instance.url)
        self.assertIn(instance.static_content_overrides['homepage_overlay_html'], homepage_html)

        page_url = instance.url + page
        server_html = get_url_contents(page_url)
        self.assertIn(instance.static_content_overrides['static_template_{}_content'.format(page)], server_html)

    @skipIf(TEST_GROUP is not None and TEST_GROUP != '1', "Test not in test group.")
    @patch("instance.models.openedx_appserver.OpenEdXAppServer.manage_instance_services")
    def test_spawn_appserver(self, manage_instance_services):
        """
        Provision an instance and spawn an AppServer, complete with custom theme (colors)
        """
        # Mock the execution of the manage_instance_services playbook as the celery workers aren't
        # set up in the playbook used for setting up the instance for this test.
        manage_instance_services.return_value = True

        OpenEdXInstanceFactory(
            name='Integration - test_spawn_appserver',
            deploy_simpletheme=True,
            static_content_overrides={
                'version': 0,
                'static_template_about_content': 'Hello world!',
                'homepage_overlay_html': '<h1>Welcome to the LMS!</h1>',
            },
        )
        instance = OpenEdXInstance.objects.get()

        # Add an lms user, as happens with beta registration
        user, _ = get_user_model().objects.get_or_create(username='test', email='test@example.com')
        instance.lms_users.add(user)

        # Create user profile and update user model from db
        UserProfile.objects.create(
            user=user,
            full_name="Test user 1",
            accepted_privacy_policy=datetime.now(),
            accept_domain_condition=True,
            subscribe_to_updates=True,
        )
        user.refresh_from_db()

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
        deployment = OpenEdXDeployment.objects.create(
            instance_id=instance.ref.id,
            creator=user.profile,
            type=DeploymentType.user.name,
            changes=None,
        )

        # We don't want to simulate e-mail verification of the user who submitted the application,
        # because that would start provisioning. Instead, we provision ourselves here.

        spawn_appserver(
            instance.ref.pk,
            mark_active_on_success=True,
            num_attempts=2,
            deployment_id=deployment.id,
            target_count=1,
            old_server_ids=[],
        )

        self.assert_server_ready(instance)
        self.assert_instance_up(instance)
        self.assert_bucket_configured(instance)
        self.assert_appserver_firewalled(instance)
        self.assertTrue(instance.successfully_provisioned)
        for appserver in instance.appserver_set.all():
            self.assert_secret_keys(instance, appserver)
            self.assert_lms_users_provisioned(user, appserver)
            self.assert_theme_provisioned(instance, appserver, application)
            self.assert_static_content_overrides_work(instance, appserver, page='about')
        self.assert_load_balanced_domains(instance)

        # Test external databases

        if settings.DEFAULT_INSTANCE_MYSQL_URL and settings.DEFAULT_INSTANCE_MONGO_URL:
            self.assertFalse(instance.require_user_creation_success())
            self.assert_mysql_db_provisioned(instance)
            self.assert_mongo_db_provisioned(instance)

        # Test activity CSV

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
        self.assertIn('"test@example.com"', out_lines[1])
        self.assertNotIn('N/A', out_lines[1])

        # stdout should contain 3 lines (as opposed to 2) to account for the last newline.
        self.assertEqual(len(out_lines), 3)

    @skipIf(TEST_GROUP is not None and TEST_GROUP != '2', "Test not in test group.")
    @patch_git_checkout
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

    @skipIf(TEST_GROUP is not None and TEST_GROUP != '2', "Test not in test group.")
    @patch("instance.models.openedx_appserver.OpenEdXAppServer.manage_instance_services")
    @patch("instance.models.openedx_appserver.OpenEdXAppServer.get_playbooks")
    @patch("instance.models.openedx_appserver.OpenEdXAppServer.heartbeat_active")
    def test_ansible_failignore(self, heartbeat_active, get_playbooks, manage_instance_services):
        """
        Ensure failures that are ignored aren't reflected in the instance
        """
        get_playbooks.return_value = [
            Playbook(
                source_repo=os.path.join(os.path.dirname(__file__), 'ansible'),
                requirements_path='requirements.txt',
                playbook_path='playbooks/failignore.yml',
                version=None,
                variables='{}',
            )
        ]

        # Mocking the manage_services.yml playbook because the services it tries to manage
        # will not be installed in the appserver provisioned by the dummy failignore.yml
        # playbook.
        manage_instance_services.return_value = True

        instance = OpenEdXInstanceFactory(
            name='Integration - test_ansible_failignore',
            configuration_playbook_name='playbooks/failignore.yml'
        )

        # Mock the heartbeat check to succeed as soon as the server's status switches to Ready.
        def is_heartbeat_active():
            appserver = instance.appserver_set.first()
            return appserver and appserver.server.status == ServerStatus.Ready

        heartbeat_active.side_effect = is_heartbeat_active

        create_new_deployment(instance, mark_active_on_success=True, num_attempts=1)
        self.assert_server_ready(instance)

    @retry
    def assert_server_terminated(self, server):
        """
        Makes sure the given server has been properly terminated.
        """
        self.assertEqual(server.update_status(), ServerStatus.Terminated)

    @skipIf(TEST_GROUP is not None and TEST_GROUP != '2', "Test not in test group.")
    def test_openstack_server_terminated(self):
        """
        Test that OpenStackServer detects if the VM was terminated externally.
        """
        server = spawn_openstack_server("integration_test")
        server.os_server.delete()
        self.assert_server_terminated(server)

    @skipIf(TEST_GROUP is not None and TEST_GROUP != '2', "Test not in test group.")
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

        # Create user profile and update user model from db
        UserProfile.objects.create(
            user=user,
            full_name="Test user 1",
            accepted_privacy_policy=datetime.now(),
            accept_domain_condition=True,
            subscribe_to_updates=True,
        )
        user.refresh_from_db()

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
