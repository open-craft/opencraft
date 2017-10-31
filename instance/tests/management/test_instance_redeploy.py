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
Instance - Redeployment task unit tests
"""
# Imports #####################################################################

from unittest.mock import patch, MagicMock
from testfixtures import log_capture, LogCapture

from django.core.management import call_command, CommandError
from django.utils.six import StringIO
from django.test import TestCase

from instance.models.instance import InstanceTag
from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.models.factories.openedx_appserver import make_test_appserver


# Tests #######################################################################

class InstanceRedeployTestCase(TestCase):
    """
    Test cases for the `instance_redeploy` management command.
    """
    def setUp(self):
        """
        Set up properties used to verify captured logs
        """
        super().setUp()
        self.cmd_module = 'instance.management.commands.instance_redeploy'
        self.log_level = 'INFO'

    def test_required_args(self):
        """
        Verify that the command correctly requires the --tag parameter
        """
        with self.assertRaisesRegex(CommandError, 'Error: the following arguments are required: --tag'):
            call_command('instance_redeploy')

    @patch('instance.management.commands.instance_redeploy.input', MagicMock(return_value='no'))
    def test_no_redeploy(self):
        """
        Verify that the user can cancel the redeployment by answering "no"
        """
        out = StringIO()
        call_command('instance_redeploy', '--tag=test-tag', stdout=out)
        self.assertEqual('Do you want to continue? [yes/No]\n', out.getvalue())

    @patch('instance.management.commands.instance_redeploy.input', MagicMock(return_value='yes'))
    def test_yes_redeploy(self):
        """
        Verify that the user can continue with the redeployment by answering "yes"
        """
        out = StringIO()
        call_command('instance_redeploy', '--tag=test-tag', stdout=out)
        self.assertEqual('Do you want to continue? [yes/No]\n', out.getvalue())

    def test_force_redeploy(self):
        """
        Verify that the user is not promped when --force is provided
        """
        out = StringIO()
        call_command('instance_redeploy', '--tag=test-tag', '--force', stdout=out)
        self.assertEqual('', out.getvalue())

    @log_capture()
    def test_default_arguments(self, captured_logs):
        """
        Verify status is logged as expected with default arguments
        """
        call_command('instance_redeploy', '--tag=test-tag', '--force')
        expected_logs = ((self.cmd_module, self.log_level, msg) for msg in (
            '******* Status *******',
            'Instances pending redeployment: 0',
            'Redeployments in progress: 0',
            'Failed to redeploy: 0',
            'Successfully redeployed (done): 0',
            'Batch size: 2',
            'Batch frequency: 0:10:00',
            'Number of upgrade attempts per instance: 1',
            '** Starting redeployment **',
            '******* Status *******',
            'Instances pending redeployment: 0',
            'Redeployments in progress: 0',
            'Failed to redeploy: 0',
            'Successfully redeployed (done): 0',
            '** Redeployment done **',
        ))
        captured_logs.check(*expected_logs)

    @staticmethod
    def create_test_instances(tag, success=True):
        """
        Create instances to test redeployments.
        """
        # Create test instances with known attributes, and mock out the appserver_set
        instances = {}
        for label in 'ABCDEFG':

            # Create an instance, with an appserver
            instance = OpenEdXInstance.objects.create(sub_domain=label, openedx_release='z.1')
            appserver = make_test_appserver(instance)

            if success:
                # Transition the appserver through the various statuses to "running"
                appserver._status_to_waiting_for_server()
                appserver._status_to_configuring_server()
                appserver._status_to_running()
            else:
                # Transition the appserver through to "error"
                appserver._status_to_waiting_for_server()
                appserver._status_to_error()

            instances[label] = dict(instance=instance, appserver=appserver)

        # Update Instance A so it no longer matches the filter
        instances['A']['instance'].openedx_release = 'y.1'
        instances['A']['instance'].save()

        # Archive Instance B, so it too won't match the filter
        instances['B']['instance'].ref.is_archived = True
        instances['B']['instance'].save()

        def _tag_instance(instance, tag_name):
            """
            Add the given named tag to the given instance.
            """
            tag, _ = InstanceTag.objects.get_or_create(name=tag_name)
            instance.tags.add(tag)
            instance.save()

        # Tag Instance C as "failed"
        _tag_instance(instances['C']['instance'], tag + '-failure')

        # Tag Instance D as "success" -- will be activated on the first redeployment loop.
        _tag_instance(instances['D']['instance'], tag + '-success')

        # Tag Instance E as "done"
        _tag_instance(instances['E']['instance'], tag)

        return instances

    @patch('instance.management.commands.instance_redeploy.spawn_appserver')
    def test_redeployment_success(self, mock_spawn_appserver):
        """
        Test the instance redeployment when everything goes well

        TODO: test update, and sql commands.
        """
        tag = 'test-tag'
        instances = self.create_test_instances(tag, success=True)

        def _spawn_appserver_success(
                instance_ref_id,
                mark_active_on_success=False,
                deactivate_old_appservers=False,
                num_attempts=1,
                success_tag=None,
                failure_tag=None):
            """
            Mock the instance.tasks.spawn_appserver method to
            instantly mark appserver as successfully spawned.
            """
            instance = OpenEdXInstance.objects.get(ref_set__pk=instance_ref_id)
            instance.tags.remove(failure_tag)
            instance.tags.add(success_tag)

        mock_spawn_appserver.side_effect = _spawn_appserver_success

        # Redeploying with batch-size=2, so we'll spawn two appservers at a time.
        expected_logs = ((self.cmd_module, self.log_level, msg) for msg in (
            '******* Status *******',
            'Instances pending redeployment: 3',
            'Redeployments in progress: 0',
            'Failed to redeploy: 1',
            'Successfully redeployed (done): 1',
            'Batch size: 2',
            'Batch frequency: 0:00:01',
            'Number of upgrade attempts per instance: 1',

            '** Starting redeployment **',
            'SPAWNING: {0} [{0.id}]'.format(instances['F']['instance']),
            'SPAWNING: {0} [{0.id}]'.format(instances['G']['instance']),

            '******* Status *******',
            'Instances pending redeployment: 1',
            'Redeployments in progress: 2',
            'Failed to redeploy: 1',
            'Successfully redeployed (done): 3',
            'Sleeping for 0:00:01',
            'SUCCESS: {0} [{0.id}]'.format(instances['F']['instance']),
            'SUCCESS: {0} [{0.id}]'.format(instances['G']['instance']),
            'SPAWNING: {0} [{0.id}]'.format(instances['E']['instance']),

            '******* Status *******',
            'Instances pending redeployment: 0',
            'Redeployments in progress: 1',
            'Failed to redeploy: 1',
            'Successfully redeployed (done): 4',
            'Sleeping for 0:00:01',
            'SUCCESS: {0} [{0.id}]'.format(instances['E']['instance']),

            '******* Status *******',
            'Instances pending redeployment: 0',
            'Redeployments in progress: 0',
            'Failed to redeploy: 1',
            'Successfully redeployed (done): 4',

            '** Redeployment done **',
        ))

        # Call the redeployment command, and verify the logs
        with LogCapture() as captured_logs:
            call_command(
                'instance_redeploy',
                '--tag=' + tag,
                '--force',
                '--batch-size=2',
                '--batch-frequency=1',
                '--filter={"openedx_release": "z.1"}',
                stdout=StringIO(),
            )
            # Verify the logs
            captured_logs.check(*expected_logs)

    @patch('instance.management.commands.instance_redeploy.spawn_appserver')
    def test_redeployment_failure(self, mock_spawn_appserver):
        """
        Test the instance redeployment when instances fail.

        TODO: test update, and sql commands.
        """
        tag = 'test-tag'
        instances = self.create_test_instances(tag, success=False)

        def _spawn_appserver_failed(
                instance_ref_id,
                mark_active_on_success=False,
                deactivate_old_appservers=False,
                num_attempts=1,
                success_tag=None,
                failure_tag=None):
            """
            Mock the instance.tasks.spawn_appserver method to
            instantly mark appserver as failed.
            """
            instance = OpenEdXInstance.objects.get(ref_set__pk=instance_ref_id)
            instance.tags.add(failure_tag)
            instance.tags.remove(success_tag)

        mock_spawn_appserver.side_effect = _spawn_appserver_failed

        # Redeploying with batch-size=1, so we'll spawn one appservers at a time.
        expected_logs = ((self.cmd_module, self.log_level, msg) for msg in (
            '******* Status *******',
            'Instances pending redeployment: 3',
            'Redeployments in progress: 0',
            'Failed to redeploy: 1',
            'Successfully redeployed (done): 1',
            'Batch size: 1',
            'Batch frequency: 0:00:01',
            'Number of upgrade attempts per instance: 1',

            '** Starting redeployment **',
            'SPAWNING: {0} [{0.id}]'.format(instances['F']['instance']),

            '******* Status *******',
            'Instances pending redeployment: 2',
            'Redeployments in progress: 1',
            'Failed to redeploy: 2',
            'Successfully redeployed (done): 1',
            'Sleeping for 0:00:01',
            'FAILED: {0} [{0.id}]'.format(instances['F']['instance']),
            'SPAWNING: {0} [{0.id}]'.format(instances['G']['instance']),

            '******* Status *******',
            'Instances pending redeployment: 1',
            'Redeployments in progress: 1',
            'Failed to redeploy: 3',
            'Successfully redeployed (done): 1',
            'Sleeping for 0:00:01',
            'FAILED: {0} [{0.id}]'.format(instances['G']['instance']),
            'SPAWNING: {0} [{0.id}]'.format(instances['E']['instance']),

            '******* Status *******',
            'Instances pending redeployment: 0',
            'Redeployments in progress: 1',
            'Failed to redeploy: 4',
            'Successfully redeployed (done): 1',
            'Sleeping for 0:00:01',
            'FAILED: {0} [{0.id}]'.format(instances['E']['instance']),

            '******* Status *******',
            'Instances pending redeployment: 0',
            'Redeployments in progress: 0',
            'Failed to redeploy: 4',
            'Successfully redeployed (done): 1',

            '** Redeployment done **',
        ))

        # Call the redeployment command, and capture the logs
        with LogCapture() as captured_logs:
            call_command(
                'instance_redeploy',
                '--tag=' + tag,
                '--force',
                '--batch-size=1',
                '--batch-frequency=1',
                '--filter={"openedx_release": "z.1"}',
                stdout=StringIO(),
            )
            # Verify the logs
            captured_logs.check(*expected_logs)
