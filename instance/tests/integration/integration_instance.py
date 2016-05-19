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
import time
from unittest.mock import patch

import requests
from django.conf import settings

from instance.models.appserver import Status as AppServerStatus
from instance.models.openedx_appserver import OpenEdXAppServer
from instance.models.openedx_instance import OpenEdXInstance
from instance.models.server import Status as ServerStatus
from instance.openstack import get_swift_connection
from instance.tests.decorators import patch_git_checkout
from instance.tests.integration.base import IntegrationTestCase
from instance.tests.integration.factories.instance import OpenEdXInstanceFactory
from instance.tasks import spawn_appserver
from opencraft.tests.utils import shard


# Tests #######################################################################

# Factory boy doesn't properly support pylint+django
#pylint: disable=no-member

class InstanceIntegrationTestCase(IntegrationTestCase):
    """
    Integration test cases for instance high-level tasks
    """
    def assert_instance_up(self, instance):
        """
        Check that the given instance is up and accepting requests
        """
        instance.refresh_from_db()
        self.assertIsNotNone(instance.active_appserver)
        self.assertEqual(instance.active_appserver.status, AppServerStatus.Running)
        self.assertEqual(instance.active_appserver.server.status, ServerStatus.Ready)
        server = instance.active_appserver.server
        attempts = 3
        while True:
            attempts -= 1
            try:
                requests.get('http://{0}'.format(server.public_ip)).raise_for_status()
                break
            except Exception:  # pylint: disable=broad-except
                if not attempts:
                    raise
            time.sleep(15)

    def assert_swift_container_provisioned(self, instance):
        """
        Verify the Swift container for the instance has been provisioned successfully.

        This is done here because we can't test provisioning Swift locally.  We also delete the
        container after the check.
        """
        if not settings.SWIFT_ENABLE:
            return
        connection = get_swift_connection()
        header = connection.head_container(instance.swift_container_name)
        self.assertEqual(header['x-container-read'], '.r:*')

    @shard(1)
    def test_spawn_appserver(self):
        """
        Provision an instance and spawn an AppServer
        """
        OpenEdXInstanceFactory(name='Integration - test_spawn_appserver')
        instance = OpenEdXInstance.objects.get()
        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=2)
        self.assert_instance_up(instance)

    @shard(2)
    def test_external_databases(self):
        """
        Ensure that the instance can connect to external databases
        """
        if not settings.INSTANCE_MYSQL_URL or not settings.INSTANCE_MONGO_URL:
            print('External databases not configured, skipping integration test')
            return
        OpenEdXInstanceFactory(name='Integration - test_external_databases', use_ephemeral_databases=False)
        instance = OpenEdXInstance.objects.get()
        spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=2)
        self.assert_swift_container_provisioned(instance)
        self.assert_instance_up(instance)

    @patch_git_checkout
    def test_ansible_failure(self, git_checkout, git_working_dir):
        """
        Ensure failures in the ansible flow are reflected in the instance
        """
        git_working_dir.return_value = os.path.join(os.path.dirname(__file__), "ansible")

        instance = OpenEdXInstanceFactory(name='Integration - test_ansible_failure')
        with patch.object(OpenEdXAppServer, 'CONFIGURATION_PLAYBOOK', new="failure"):
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
        with patch.object(OpenEdXAppServer, 'CONFIGURATION_PLAYBOOK', new="failignore"):
            spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=1)
        instance.refresh_from_db()
        self.assertIsNotNone(instance.active_appserver)
        self.assertEqual(instance.active_appserver.status, AppServerStatus.Running)
        self.assertEqual(instance.active_appserver.server.status, ServerStatus.Ready)
