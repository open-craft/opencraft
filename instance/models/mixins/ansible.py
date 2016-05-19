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
Instance app model mixins - Ansible
"""

# Imports #####################################################################

from collections import namedtuple
import os

from django.conf import settings
from django.db import models

from instance import ansible
from instance.repo import open_repository
from instance.utils import poll_streams


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
    class Meta:
        abstract = True

    def get_playbooks(self):  # pylint: disable=no-self-use
        """
        Get a list of Playbook objects which describe the playbooks to run in order to install
        apps onto this AppServer.

        Subclasses should override this like:
            return super().get_playbooks + [
                Playbook(source_repo="...", ...)
            ]
        """
        return []

    @property
    def inventory_str(self):
        """
        The ansible inventory (list of servers) as a string
        """
        public_ip = self.server.public_ip
        if public_ip is None:
            raise RuntimeError("Cannot prepare to run playbooks when server has no public IP.")
        return '[app]\n{server_ip}'.format(server_ip=public_ip)

    def _run_playbook(self, working_dir, playbook):
        """
        Run a playbook against the AppServer's VM
        """
        playbook_path = os.path.join(working_dir, playbook.playbook_path)

        log_lines = []
        with ansible.run_playbook(
            requirements_path=os.path.join(working_dir, playbook.requirements_path),
            inventory_str=self.inventory_str,
            vars_str=playbook.variables,
            playbook_path=os.path.dirname(playbook_path),
            playbook_name=os.path.basename(playbook_path),
            username=settings.OPENSTACK_SANDBOX_SSH_USERNAME,
        ) as process:
            try:
                log_line_generator = poll_streams(
                    process.stdout,
                    process.stderr,
                    line_timeout=settings.ANSIBLE_LINE_TIMEOUT,
                    global_timeout=settings.ANSIBLE_GLOBAL_TIMEOUT,
                )
                for f, line in log_line_generator:
                    line = line.decode('utf-8').rstrip()
                    if f == process.stdout:
                        self.logger.info(line)
                    elif f == process.stderr:
                        self.logger.error(line)
                    log_lines.append(line)
            except TimeoutError:
                self.logger.error('Playbook run timed out.  Terminating the Ansible process.')
                process.terminate()
            process.wait()
            return log_lines, process.returncode

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

        if returncode == 0:
            self.logger.info('Playbooks completed for AppServer %s', self)
        return (log, returncode)
