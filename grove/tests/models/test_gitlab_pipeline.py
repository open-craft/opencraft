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
GitlabPipeline model - Tests
"""
from django.conf import settings
from django.test import TestCase

from grove.models.gitlabpipeline import GitlabPipeline
from grove.tests.models.factories.gitlabpipeline import GitlabPipelineFactory
from grove.tests.models.factories.grove_instance import GroveInstanceFactory
from instance.models.openedx_deployment import DeploymentState


class TestGitlabPipeline(TestCase):
    """
    Tests for methods on the GitlabPipeline model
    """
    def test_default_status(self):
        """
        Test the default pipeline status
        """
        instance = GroveInstanceFactory(
            internal_lms_domain='sample.example.org',
            edx_platform_commit=settings.DEFAULT_OPENEDX_RELEASE
        )
        new_pipeline = GitlabPipelineFactory(
            pipeline_id=1, instance=instance.ref
        )
        self.assertEqual(new_pipeline.status, GitlabPipeline.CREATED)

    def test_update_status(self):
        """
        Test for the update_status method
        """
        instance = GroveInstanceFactory(
            internal_lms_domain='sample.example.org',
            edx_platform_commit=settings.DEFAULT_OPENEDX_RELEASE
        )
        pipeline = GitlabPipelineFactory(
            pipeline_id=1, instance=instance.ref
        )
        self.assertEqual(pipeline.status, GitlabPipeline.CREATED)
        new_status = 'success'
        pipeline.update_status(new_status)
        self.assertEqual(pipeline.status, GitlabPipeline.SUCCESS)

    def test_get_deployment_status(self):
        """
        Test for the get_deployment_status method
        """
        instance = GroveInstanceFactory(
            internal_lms_domain='sample.example.org',
            edx_platform_commit=settings.DEFAULT_OPENEDX_RELEASE
        )
        pipeline = GitlabPipelineFactory(
            pipeline_id=1, instance=instance.ref
        )
        default_deployment_status = pipeline.get_deployment_status()
        self.assertEqual(default_deployment_status, DeploymentState.provisioning)
        new_status = 'success'
        pipeline.update_status(new_status)
        new_deployment_status = pipeline.get_deployment_status()
        self.assertEqual(new_deployment_status, DeploymentState.healthy)
