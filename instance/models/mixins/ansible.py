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
Instance app model mixins - Ansible
"""
import os
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.template import loader

from instance import ansible
from instance.repo import open_repository
from instance.utils import poll_streams


class AnsibleInstanceMixin(models.Model):
    """
    An instance that relies on Ansible to deploy its services
    """
    ansible_source_repo_url = models.URLField(max_length=256, blank=True)
    configuration_version = models.CharField(max_length=50, blank=True)
    ansible_playbook_name = models.CharField(max_length=50, default='edx_sandbox')
    ansible_extra_settings = models.TextField(blank=True)
    ansible_settings = models.TextField(blank=True)

    attempts = models.SmallIntegerField(default=3, validators=[
        MinValueValidator(1),
    ])

    # List of attributes to include in the settings output
    ANSIBLE_SETTINGS = ['ansible_extra_settings']

    class Meta:
        abstract = True

    def save(self, **kwargs):
        """
        Set default values before saving the instance.
        """
        # Set default field values from settings - using the `default` field attribute confuses
        # automatically generated migrations, generating a new one when settings don't match
        if not self.ansible_source_repo_url:
            self.ansible_source_repo_url = settings.DEFAULT_CONFIGURATION_REPO_URL
        if not self.configuration_version:
            self.configuration_version = settings.DEFAULT_CONFIGURATION_VERSION
        super().save(**kwargs)

    @property
    def ansible_playbook_filename(self):
        """
        File name of the ansible playbook
        """
        return '{}.yml'.format(self.ansible_playbook_name)

    @property
    def inventory_str(self):
        """
        The ansible inventory (list of servers) as a string
        """
        inventory = ['[app]']
        server_model = self.server_set.model
        for server in self.server_set.filter(status=server_model.PROVISIONING,
                                             progress=server_model.PROGRESS_RUNNING)\
                                     .order_by('created'):
            inventory.append(server.public_ip)
        inventory_str = '\n'.join(inventory)
        self.logger.debug('Inventory:\n%s', inventory_str)
        return inventory_str

    def reset_ansible_settings(self, commit=True):
        """
        Set the ansible_settings field from the Ansible vars template.
        """
        template = loader.get_template('instance/ansible/vars.yml')
        vars_str = template.render({
            'instance': self,
            # This proerty is needed twice in the template.  To avoid evaluating it twice (and
            # querying the Github API twice), we pass it as a context variable.
            'github_admin_username_list': self.github_admin_username_list,
        })
        for attr_name in self.ANSIBLE_SETTINGS:
            additional_vars = getattr(self, attr_name)
            vars_str = ansible.yaml_merge(vars_str, additional_vars)
        self.logger.debug('Vars.yml:\n%s', vars_str)
        self.ansible_settings = vars_str
        if commit:
            self.save()

    def _run_playbook(self, requirements_path, playbook_path):
        """
        Run a playbook against the instance active servers
        """
        log_lines = []
        with ansible.run_playbook(
            requirements_path,
            self.inventory_str,
            self.ansible_settings,
            playbook_path,
            self.ansible_playbook_filename,
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

    def deploy(self):
        """
        Deploy instance to the active servers
        """
        for attempt in range(self.attempts):
            with open_repository(self.ansible_source_repo_url,
                                 ref=self.configuration_version) as configuration_repo:
                playbook_path = os.path.join(configuration_repo.working_dir,
                                             'playbooks')
                requirements_path = os.path.join(configuration_repo.working_dir,
                                                 'requirements.txt')

                log = ('Running playbook "{path}/{name}" attempt {attempt} of '
                       '{attempts}:').format(
                           path=playbook_path,
                           name=self.ansible_playbook_name,
                           attempts=self.attempts,
                           attempt=attempt + 1)
                self.logger.info(log)
                log, returncode = self._run_playbook(requirements_path, playbook_path)
                if returncode != 0:
                    self.logger.error(
                        'Playbook failed for instance {}'.format(self))
                    continue
                else:
                    break

        if returncode == 0:
            self.logger.info('Playbook completed for instance {}'.format(self))
        return (log, returncode)
