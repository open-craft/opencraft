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
Instance app model mixins - Ansible
"""

# Imports #####################################################################

from collections import namedtuple
import os
import yaml

from django.conf import settings
from django.db import models

from instance import ansible
from instance.repo import open_repository


# Classes #####################################################################

Playbook = namedtuple('Playbook', [
    'source_repo',  # Path or URL to a git repository containing the playbook to run
    'playbook_path',  # Relative path to the playbook within source_repo
    'requirements_path',  # Relative path to a python requirements file to install before running the playbook
    'version',  # The git tag/commit hash/branch to use
    'variables',  # A YAML string containing extra variables to pass to ansible when running this playbook
])


class AnsibleAppServerMixin(models.Model):
    """
    An AppServer that relies on Ansible to deploy its services
    """

    common_configuration_settings = models.TextField(
        blank=True,
        help_text='YAML variables for commonly needed services.')

    INVENTORY_GROUP = 'generic'
    # It is possible to get an IP address that has already appeared, so we want to disable strict host key checking.
    HOST_ARGS = 'ansible_ssh_common_args="-o StrictHostKeyChecking=no"'

    class Meta:
        abstract = True

    def get_playbooks(self):
        """
        Get a list of Playbook objects which describe the playbooks to run in order to install
        apps onto this AppServer.

        Subclasses should override this like:
            return [
                Playbook(source_repo="...", ...)
            ] + super().get_playbooks()
        """
        return [
            Playbook(
                source_repo=settings.ANSIBLE_APPSERVER_REPO,
                requirements_path=settings.ANSIBLE_APPSERVER_REQUIREMENTS_PATH,
                playbook_path=settings.ANSIBLE_APPSERVER_PLAYBOOK,
                version=settings.ANSIBLE_APPSERVER_VERSION,
                variables=self.create_common_configuration_settings(),
            ),
        ]

    def create_common_configuration_settings(self):
        """
        Generate YML settings for common Ansible configuration.

        Note that this will bring in all configuration the particular appserver has to offer.
        """
        return yaml.dump(self._get_common_configuration_variables(), default_flow_style=False)

    @property
    def inventory_str(self):
        """
        The ansible inventory (list of servers) as a string
        """
        public_ip = self.server.public_ip
        if public_ip is None:
            raise RuntimeError("Cannot prepare to run playbooks when server has no public IP.")
        return (
            '[{group}]\n'
            '{server_ip} {host_args}\n'
            '[app:children]\n'
            '{group}'.format(group=self.INVENTORY_GROUP, server_ip=public_ip, host_args=self.HOST_ARGS)
        )

    def _run_playbook(self, working_dir, playbook):
        """
        Run a playbook against the AppServer's VM
        """
        return ansible.capture_playbook_output(
            requirements_path=os.path.join(working_dir, playbook.requirements_path),
            inventory_str=self.inventory_str,
            vars_str=playbook.variables,
            playbook_path=os.path.join(working_dir, playbook.playbook_path),
            username=settings.OPENSTACK_SANDBOX_SSH_USERNAME,
            logger_=self.logger,
            collect_logs=True,
        )

    def run_ansible_playbooks(self):
        """
        Provision the server using ansible
        """
        log = []
        for playbook in self.get_playbooks():
            with open_repository(playbook.source_repo, ref=playbook.version) as configuration_repo:
                self.logger.info('Running playbook "%s" from "%s"', playbook.playbook_path, playbook.source_repo)
                playbook_log, returncode = self._run_playbook(configuration_repo.working_dir, playbook)
                log += playbook_log
                if returncode != 0:
                    self.logger.error('Playbook failed for AppServer %s', self)
                    break
        else:
            self.logger.info('Playbooks completed for AppServer %s', self)
        return (log, returncode)

    def save(self, **kwargs):  # pylint: disable=arguments-differ
        """Save this AnsibleAppServer."""
        if not self.pk:
            self.common_configuration_settings = self.create_common_configuration_settings()
        super().save(**kwargs)
