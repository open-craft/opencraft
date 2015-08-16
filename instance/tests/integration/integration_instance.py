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

import uuid

from instance.models.instance import OpenEdXInstance
from instance.tests.integration.base import IntegrationTestCase
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
        uid = str(uuid.uuid4())[:8]
        instance = OpenEdXInstance.objects.create(
            sub_domain='{}.integration'.format(uid),
            name='Integration - test_provision_instance',
            fork_name='edx/edx-platform',
            ref_type='tags',
            branch_name='named-release/cypress', # Use a known working version
            configuration_version='named-release/cypress',
            forum_version='named-release/cypress',
            notifier_version='named-release/cypress',
            xqueue_version='named-release/cypress',
            certs_version='named-release/cypress',
        )
        provision_instance(instance.pk)
        self.assertEqual(instance.status, 'ready')
