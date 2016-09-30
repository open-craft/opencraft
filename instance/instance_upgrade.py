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
Helper functions to upgrade production instances

Contents:
    * DogwoodToEucalyptus1 - updates Dogwood to Eucalyptus.1 (major release)
    * Eucalyptus1toEucalyptus2 - updates Eucalyptus.1 to Eucalyptus.2 (minor release)
"""

from collections import namedtuple
import logging

from django.conf import settings

from instance.models.openedx_instance import OpenEdXInstance
from instance.tasks import spawn_appserver

logger = logging.getLogger(__name__)


GitVersionSpec = namedtuple("GitVersionSpec", ["url", "revision"])

DEFAULT_EDX_PLATFORM_REPO = getattr(settings, "STABLE_EDX_PLATFORM_REPO_URL", "https://github.com/edx/edx-platform")
DEFAULT_CONFIGURATION_REPO = getattr(settings, "STABLE_CONFIGURATION_REPO_URL", "https://github.com/edx/configuration")


class InstanceUpgrade(object):
    """
    Generic (abstract) class providing common functionality to instance upgrades
    """
    INITIAL_RELEASE = None
    TARGET_RELEASE = None

    EDX_PLATFORM_SPEC = GitVersionSpec(DEFAULT_EDX_PLATFORM_REPO, "release")
    CONFIGURATION_SPEC = GitVersionSpec(DEFAULT_CONFIGURATION_REPO, "release")

    def get_instances_to_upgrade(self):
        """
        Obtains list of instances to be upgraded
        """
        return OpenEdXInstance.objects.filter(  # Select instances
            active_appserver___status="running",  # that are running
            openedx_release__contains=self.INITIAL_RELEASE,  # on {INITIAL_INSTANCE}
            use_ephemeral_databases=False,  # and use persistent databases.
        )

    def upgrade_instance(self, instance):
        """
        Upgrades single instance. Should not call instance.save() as it is handled in caller.
        """
        raise NotImplementedError("Must be overridden in descendant class")

    @classmethod
    def set_git_specs(cls, instance):
        """
        Updates instance's edx-platform and configuration repositories data (URL and revision)
        """
        instance.edx_platform_repository_url = cls.EDX_PLATFORM_SPEC.url
        instance.edx_platform_commit = cls.EDX_PLATFORM_SPEC.revision

        instance.configuration_source_repo_url = cls.CONFIGURATION_SPEC.url
        instance.configuration_version = cls.CONFIGURATION_SPEC.revision

    @staticmethod
    def replace_extra_config(instance, target, replacement):
        """
        Replaces part of configuration_extra_settings with other string.
        """
        instance.configuration_extra_settings = instance.configuration_extra_settings.replace(target, replacement)

    @classmethod
    def clean_up_after_upgrade(cls, instances):
        """
        Should be invoked after all instances are updated
        """
        pass

    def upgrade_instances(self):
        """
        Main upgrade method:
        1. Obtains list of instances to upgrade
        2. Updates instances' fields
        3. Saves updated instances to DB
        4. Schedules jobs to spawn new appservers with new instance settings
        """
        instances = self.get_instances_to_upgrade()

        for instance in instances:
            instance.refresh_from_db()
            logger.info("Upgrading instance %s to %s ...", instance, self.TARGET_RELEASE)
            self.upgrade_instance(instance)
            instance.save()
            spawn_appserver(instance.ref.pk, mark_active_on_success=True, num_attempts=1)

        # TODO: schedule clean_up_after_upgrade after instances are updated (huey task with conditional?)


class DogwoodToEucalyptus1(InstanceUpgrade):
    """
    Upgrade from Dogwood to Eucalyptus.1
    """
    INITIAL_RELEASE = "dogwood"
    REVISION = "opencraft-release/eucalyptus.1"
    TARGET_RELEASE = REVISION

    EDX_PLATFORM_SPEC = GitVersionSpec("https://github.com/open-craft/edx-platform", REVISION)
    CONFIGURATION_SPEC = GitVersionSpec("https://github.com/open-craft/configuration", REVISION)

    def upgrade_instance(self, instance):
        """Update instance fields to Eucalyptus.1 values"""
        self.set_git_specs(instance)
        instance.configuration_extra_settings += "\nCOMMON_EUCALYPTUS_UPGRADE: true\n"
        instance.openedx_release = "open-release/eucalyptus.1"

    @classmethod
    def clean_up_after_upgrade(cls, instances):
        """Remove Eucalyptus upgrade flag from the instance configuration."""
        for instance in instances:
            instance.refresh_from_db()
            cls.replace_extra_config(instance, "\nCOMMON_EUCALYPTUS_UPGRADE: true\n", "")
            instance.save()


class Eucalyptus1toEucalyptus2(InstanceUpgrade):
    """
    Upgrade from Eucalyptus.1 to Eucalyptus.2
    """
    INITIAL_RELEASE = "eucalyptus.1"

    REVISION = "opencraft-release/eucalyptus.2"
    TARGET_RELEASE = REVISION

    EDX_PLATFORM_SPEC = GitVersionSpec("https://github.com/open-craft/edx-platform", REVISION)
    CONFIGURATION_SPEC = GitVersionSpec("https://github.com/open-craft/configuration", REVISION)

    def upgrade_instance(self, instance):
        """Update instance fields to Eucalyptus.2 values"""
        self.set_git_specs(instance)
        self.replace_extra_config(instance, "\nCOMMON_EUCALYPTUS_UPGRADE: true\n", "")
        instance.openedx_release = "open-release/eucalyptus.2"
