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
Instance Upgrade - Tests
"""
from unittest.mock import call, patch, Mock
import ddt

from instance.instance_upgrade import InstanceUpgrade, DogwoodToEucalyptus1, GitVersionSpec, Eucalyptus1toEucalyptus2
from instance.models.openedx_instance import OpenEdXInstance
from instance.tests.base import TestCase


class BaseInstanceUpgradeTest(TestCase):
    """
    Base class for instance upgrade tests
    """
    def setUp(self):
        """
        Test setup
        """
        super(BaseInstanceUpgradeTest, self).setUp()
        self.instance_objects_mock = self._apply_patch(OpenEdXInstance, patch_attribute='objects')
        self.spawn_appserver_mock = self._apply_patch("instance.instance_upgrade.spawn_appserver")

    def _apply_patch(self, target, patch_attribute=None, **kwargs):
        """
        Patches specified `target`, registers patch to be removed in test cleanup and returns patch object for
        future interaction
        """
        patched_object = Mock()
        if patch_attribute:
            patcher = patch.object(target, patch_attribute, new=patched_object, **kwargs)
        else:
            patcher = patch(target, new=patched_object, **kwargs)
        patcher.start()
        self.addCleanup(patcher.stop)  # addCleanup expects function, so missing () after stop is not a bug
        return patched_object

    @staticmethod
    def _make_instance_mock():
        """
        Helper method - creates instance mock
        """
        mock = Mock(spec=OpenEdXInstance)
        # for some reason Mock can't find these attributes automatically and raises AttributeErrors
        mock.edx_platform_repository_url = None
        mock.edx_platform_commit = None
        mock.configuration_source_repo_url = None
        mock.configuration_version = None
        mock.configuration_extra_settings = ""

        return mock

    def _assert_git_specs(self, instance, platform_spec, config_spec, not_equal=False):
        """
        Helper method to check git configuration specs
        """
        assertion = self.assertNotEqual if not_equal else self.assertEqual

        assertion(instance.edx_platform_repository_url, platform_spec.url)
        assertion(instance.edx_platform_commit, platform_spec.revision)
        assertion(instance.configuration_source_repo_url, config_spec.url)
        assertion(instance.configuration_version, config_spec.revision)

    @staticmethod
    def _make_git_spec(url, revision):
        """
        Helper method to construct GitVersionSpec
        """
        return GitVersionSpec(url, revision)


@ddt.ddt
class TestInstanceUpgrade(BaseInstanceUpgradeTest):
    """
    Tests for generic instance upgrade functionality
    """

    class DummyInstanceUpgrade(InstanceUpgrade):
        """
        InstanceUpgrade class is intended to be abstract; this class provides simplest implementation possible
        """
        INITIAL_RELEASE = "QWERTY"
        TARGET_RELEASE = "ASDFGH"

        def upgrade_instance(self, instance):
            """
            Upgrade single instance
            """
            pass

    def setUp(self):
        """
        Test set up method
        """
        super(TestInstanceUpgrade, self).setUp()
        self.upgrader = self.DummyInstanceUpgrade()

    def test_get_instances_to_upgrade(self):
        """
        Test get_instances_to_upgrade
        """
        expected_instances = ['instance1', 'instance2', 'instance3']
        self.instance_objects_mock.filter.return_value = expected_instances
        actual_instances = self.upgrader.get_instances_to_upgrade()

        self.assertEqual(actual_instances, expected_instances)
        self.instance_objects_mock.filter.assert_called_once_with(
            active_appserver___status="running",
            openedx_release__contains=self.DummyInstanceUpgrade.INITIAL_RELEASE,
            use_ephemeral_databases=False
        )

    def test_set_git_specs(self):
        """
        Test updating git specs
        """
        instance_mock = self._make_instance_mock()
        self.upgrader.set_git_specs(instance_mock)

        expected_platform_spec = self.DummyInstanceUpgrade.EDX_PLATFORM_SPEC
        expected_config_spec = self.DummyInstanceUpgrade.CONFIGURATION_SPEC

        self._assert_git_specs(instance_mock, expected_platform_spec, expected_config_spec)

    @ddt.unpack
    @ddt.data(
        ("", "", "", ""),  # empty
        ("Test", "Test", "Hit", "Hit"),  # replacement hit
        ("Test", "Miss", "Miss", "Test"),  # replacement miss
        ("ASD\nZXC", "ASD", "QWE", "QWE\nZXC"),  # multiline replacement - single hit
        ("ASD\nASD", "ASD", "QWE", "QWE\nQWE"),  # multiline replacement - multiple hits
        ("ASD\nASD", "ASD\n", "", "ASD"),  # remove line
    )
    def test_replace_extra_config(self, initial_settings, target, replacement, expected_settings):
        """
        Test changing configuration_extra_settings
        """
        instance_mock = self._make_instance_mock()
        instance_mock.configuration_extra_settings = initial_settings
        self.upgrader.replace_extra_config(instance_mock, target, replacement)
        self.assertEqual(instance_mock.configuration_extra_settings, expected_settings)

    def test_upgrade_instances(self):
        """
        Test upgrading multiple instances
        """
        instances_collection = [self._make_instance_mock() for _ in range(3)]

        with patch.object(self.upgrader, 'get_instances_to_upgrade') as patched_get_instances, \
                patch.object(self.upgrader, 'upgrade_instance') as patched_upgrade_instance:
            patched_get_instances.return_value = instances_collection
            self.upgrader.upgrade_instances()

            for instance in instances_collection:
                instance.save.assert_called_once_with()

            expected_upgrade_instance_calls = [call(instance) for instance in instances_collection]
            self.assertEqual(patched_upgrade_instance.mock_calls, expected_upgrade_instance_calls)

            expected_spawn_calls = [
                call(instance.ref.pk, mark_active_on_success=True, num_attempts=1)
                for instance in instances_collection
            ]
            self.assertEqual(self.spawn_appserver_mock.mock_calls, expected_spawn_calls)


class TestDogwoodToEucalyptus1(BaseInstanceUpgradeTest):
    """
    Test upgrade from dogwood to eucalyptus.1
    """
    def setUp(self):
        """
        Test set up method
        """
        super(TestDogwoodToEucalyptus1, self).setUp()
        self.upgrader = DogwoodToEucalyptus1()

    def test_upgrade_instance(self):
        """
        Test upgrading single instance
        """
        instance_mock = self._make_instance_mock()
        revision = "opencraft-release/eucalyptus.1"
        expected_platform_spec = self._make_git_spec("https://github.com/open-craft/edx-platform", revision)
        expected_config_spec = self._make_git_spec("https://github.com/open-craft/configuration", revision)

        # precondition check
        self._assert_git_specs(instance_mock, expected_platform_spec, expected_config_spec, not_equal=True)

        self.upgrader.upgrade_instance(instance_mock)
        self._assert_git_specs(instance_mock, expected_platform_spec, expected_config_spec)
        self.assertIn("\nCOMMON_EUCALYPTUS_UPGRADE: true\n", instance_mock.configuration_extra_settings)
        self.assertEqual(instance_mock.openedx_release, "open-release/eucalyptus.1")

    def test_clean_up_after_upgrade(self):
        """
        Test cleaning instances after upgrade
        """
        instance_mock = self._make_instance_mock()

        # double newline after SOMETHING is not a typo - cleanup assumes empty newline before COMMON_EUCALYPTUS_UPGRADE
        instance_mock.configuration_extra_settings = "SOMETHING\n\nCOMMON_EUCALYPTUS_UPGRADE: true\nSOMETHING_ELSE"

        self.upgrader.clean_up_after_upgrade([instance_mock])
        self.assertEqual(instance_mock.configuration_extra_settings, "SOMETHING\nSOMETHING_ELSE")


class TestEucalyptus1toEucalyptus2(BaseInstanceUpgradeTest):
    """
    Test upgrade from eucalyptus.1 to eucalyptus.2
    """
    def setUp(self):
        """
        Test set up method (oh how I'm tired to repeat it again and again and again)
        """
        super(TestEucalyptus1toEucalyptus2, self).setUp()
        self.upgrader = Eucalyptus1toEucalyptus2()

    def test_upgrade_instance(self):
        """
        Test upgrading single instance
        """
        instance_mock = self._make_instance_mock()
        revision = "opencraft-release/eucalyptus.2"
        expected_platform_spec = self._make_git_spec("https://github.com/open-craft/edx-platform", revision)
        expected_config_spec = self._make_git_spec("https://github.com/open-craft/configuration", revision)

        # precondition check
        self._assert_git_specs(instance_mock, expected_platform_spec, expected_config_spec, not_equal=True)

        self.upgrader.upgrade_instance(instance_mock)
        self._assert_git_specs(instance_mock, expected_platform_spec, expected_config_spec)
        self.assertNotIn("COMMON_EUCALYPTUS_UPGRADE", instance_mock.configuration_extra_settings)
        self.assertEqual(instance_mock.openedx_release, "open-release/eucalyptus.2")
