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
Instance app - instances' metadata update management command
"""
# Imports #####################################################################
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.utils.six import StringIO
from django.test import TestCase, override_settings

import consul


# Tests #######################################################################
from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.utils import skip_unless_consul_running


@skip_unless_consul_running()
class UpdateMetadataTestCase(TestCase):
    """
    Test cases for the `update_metadata` management command.
    """
    def setUp(self):
        self.client = consul.Consul()
        if self.client.kv.get('', recurse=True)[1]:
            self.skipTest('Consul contains unknown values!')

    @override_settings(CONSUL_ENABLED=False)
    def test_consul_not_enabled(self):
        """
        Verify that the command exits if Consul is not enabled from the
        settings file.
        """
        out = StringIO()
        with self.assertRaises(SystemExit):
            call_command('update_metadata', stdout=out)

        self.assertIn(
            'This command does nothing unless you enable Consul in the configuration. Exiting..',
            out.getvalue()
        )

    @override_settings(CONSUL_ENABLED=True)
    @patch('instance.management.commands.update_metadata.OpenEdXInstance.update_consul_metadata')
    def test_consul_skip_clean(self, update_consul_metadata):
        """
        Tests the management command with skipping metadata clean option.

        :param update_consul_metadata: update_consul_metadata method mock
        """

        update_consul_metadata.return_value = 1, True
        out = StringIO()

        total_instances = 0
        call_command('update_metadata', skip_clean=True, stdout=out)

        self.assertIn('Updating {} instances\' metadata'.format(total_instances), out.getvalue())
        self.assertIn('Successfully updated instances\' metadata', out.getvalue())
        self.assertNotIn('Cleaning metadata for {} archived instances...'.format(total_instances), out.getvalue())

    @override_settings(CONSUL_ENABLED=True)
    def test_consul_skip_update(self):
        """
        Tests the management command with skipping metadata update option.

        :param purge_consul_metadata: purge_consul_metadata method mock
        """
        out = StringIO()

        # Archive the instances
        instances = [OpenEdXInstanceFactory.create() for _ in range(10)]
        for instance in instances:
            instance.ref.is_archived = True
            instance.ref.save()

        # Add some garbage data to consul
        bad_prefix = settings.CONSUL_PREFIX.format(ocim=settings.OCIM_ID, instance=333)
        self.client.kv.put(bad_prefix + 'key1', 'value1')
        self.client.kv.put(bad_prefix + 'key2', 'value2')

        call_command('update_metadata', skip_update=True, stdout=out)
        objects_count = OpenEdXInstance.objects.count()

        self.assertIn('Cleaning metadata for {} archived instances...'.format(objects_count + 1), out.getvalue())
        self.assertIn('Successfully cleaned archived instances\' metadata', out.getvalue())
        self.assertNotIn('Updating {} instances\' metadata'.format(objects_count + 1), out.getvalue())

    @override_settings(CONSUL_ENABLED=True)
    def test_consul_no_skip(self):
        """
        Tests the management command without skipping metadata update or clean options.

        :param purge_consul_metadata: purge_consul_metadata method mock
        :param update_consul_metadata: update_consul_metadata method mock
        """
        out = StringIO()

        # Archive the instances
        total_archived_instances = 10
        archived_instances = [OpenEdXInstanceFactory.create() for _ in range(total_archived_instances)]
        for instance in archived_instances:
            instance.ref.is_archived = True
            instance.ref.save()

        # Add some garbage data to consul
        bad_prefix = settings.CONSUL_PREFIX.format(ocim=settings.OCIM_ID, instance=333)
        self.client.kv.put(bad_prefix + 'key1', 'value1')
        self.client.kv.put(bad_prefix + 'key2', 'value2')

        # Create an active instance
        active_instances_total = 20
        _ = [OpenEdXInstanceFactory.create() for _ in range(active_instances_total)]

        call_command('update_metadata', stdout=out)

        self.assertIn('Updating {} instances\' metadata'.format(active_instances_total), out.getvalue())
        self.assertIn('Successfully updated instances\' metadata', out.getvalue())
        self.assertIn(
            'Cleaning metadata for {} archived instances...'.format(total_archived_instances + 1),
            out.getvalue()
        )
        self.assertIn('Successfully cleaned archived instances\' metadata', out.getvalue())

    def tearDown(self):
        self.client.kv.delete('', recurse=True)
