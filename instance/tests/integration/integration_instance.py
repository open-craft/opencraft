# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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

from instance.models.instance import OpenEdXInstance
from instance.tests.decorators import patch_git_checkout
from instance.tests.integration.base import IntegrationTestCase
from instance.tests.integration.factories.instance import OpenEdXInstanceFactory
from instance.tasks import provision_instance


# Tests #######################################################################

class InstanceIntegrationTestCase(IntegrationTestCase):
    """
    Integration test cases for instance high-level tasks
    """
    def test_provision_instance(self):
        """
        Provision an instance
        """
        OpenEdXInstanceFactory(name='Integration - test_provision_instance')
        instance = OpenEdXInstance.objects.get()
        provision_instance(instance.pk)
        self.assertEqual(instance.status, 'ready')

    @patch_git_checkout
    def test_ansible_failure(self, git_checkout, git_working_dir):
        """
        Ensure failures in the ansible flow are reflected in the instance
        """
        git_working_dir.return_value = os.path.join(os.path.dirname(__file__), "ansible")

        OpenEdXInstanceFactory(name='Integration - test_ansible_failure',
                               ansible_playbook_name='failure')
        instance = OpenEdXInstance.objects.get()
        provision_instance(instance.pk)
        self.assertEqual(instance.status, OpenEdXInstance.PROVISIONING)
        self.assertEqual(instance.progress, OpenEdXInstance.PROGRESS_FAILED)

    @patch_git_checkout
    def test_ansible_failignore(self, git_checkout, git_working_dir):
        """
        Ensure failures that are ignored doesn't reflect in the instance
        """
        git_working_dir.return_value = os.path.join(os.path.dirname(__file__), "ansible")

        OpenEdXInstanceFactory(name='Integration - test_ansible_failignore',
                               ansible_playbook_name='failignore')
        instance = OpenEdXInstance.objects.get()
        provision_instance(instance.pk)
        self.assertEqual(instance.status, OpenEdXInstance.READY)
        self.assertEqual(instance.progress, OpenEdXInstance.PROGRESS_SUCCESS)
