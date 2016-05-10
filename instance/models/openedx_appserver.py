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
Instance app models - Open EdX AppServer models
"""
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.template import loader
from django.utils.text import slugify
from swampdragon.pubsub_providers.data_publisher import publish_data

from instance import ansible
from instance.logging import log_exception
from instance.models.appserver import AppServer
from instance.models.mixins.ansible import AnsibleAppServerMixin, Playbook
from instance.models.mixins.utilities import EmailMixin
from instance.models.utils import format_help_text
from pr_watch.github import get_username_list_from_team

# Constants ###################################################################

PROTOCOL_CHOICES = (
    ('http', 'HTTP - Unencrypted clear text'),
    ('https', 'HTTPS - Encrypted'),
)

DEFAULT_EDX_PLATFORM_REPO_URL = 'https://github.com/{}.git'.format(settings.DEFAULT_FORK)

# Models ######################################################################


class OpenEdXAppConfiguration(models.Model):
    """
    Configuration fields used by OpenEdX Instance and AppServer.

    Mutable on the instance but immutable on the AppServer.
    """
    class Meta:
        abstract = True

    email = models.EmailField(default='contact@example.com', help_text=(
        'The default contact email for this instance; also used as the from address for emails '
        'sent by the server.'
    ))
    protocol = models.CharField(max_length=5, default='http', choices=PROTOCOL_CHOICES)

    # Ansible-specific settings:
    configuration_source_repo_url = models.URLField(max_length=256, blank=False)
    configuration_version = models.CharField(max_length=50, blank=False)
    configuration_extra_settings = models.TextField(blank=True, help_text="YAML config vars that override all others")

    edx_platform_repository_url = models.CharField(max_length=256, blank=False, help_text=(
        'URL to the edx-platform repository to use. Leave blank for default.'
    ))
    edx_platform_commit = models.CharField(max_length=256, blank=False, help_text=(
        'edx-platform commit hash or branch or tag to use. Leave blank to use the default, '
        'which is equal to the value of "openedx_release".'
    ))

    openedx_release = models.CharField(max_length=128, blank=False, help_text=format_help_text("""
        Set this to a release tag like "named-release/dogwood" to build a specific release of
        Open edX. This setting becomes the default value for edx_platform_version,
        forum_version, notifier_version, xqueue_version, and certs_version so it should be a git
        branch that exists in all of those repositories.

        Note: to build a specific branch of edx-platform, you should just override
        edx_platform_commit rather than changing this setting.

        Note 2: This value does not affect the default value of configuration_version.
    """))

    # Misc settings:
    use_ephemeral_databases = models.BooleanField()
    github_admin_organization_name = models.CharField(
        max_length=200, blank=True, default=settings.DEFAULT_ADMIN_ORGANIZATION,
        help_text="GitHub organization whose users will be given SSH access to this instance's VMs",
    )

    @classmethod
    def get_config_fields(cls):
        """
        Get the names of each field declared on this model (except the automatic ID field).

        This is used to copy the current values from an Instance to an AppServer when creating
        a new AppServer.
        """
        return [field.name for field in cls._meta.fields if field.name not in ('id', )]


class OpenEdXAppServer(AppServer, OpenEdXAppConfiguration, AnsibleAppServerMixin, EmailMixin):
    """
    OpenEdXAppServer: One or more of the Open edX apps, running on a single VM

    Typically, most of the Open edX apps are enabled, including but not limited to:
    * edxapp (LMS+Studio)
    * cs_comments_service (forums)
    * notifier
    * xqueue
    * insights
    """
    configuration_database_settings = models.TextField(blank=True, help_text="YAML vars for database configuration")
    configuration_storage_settings = models.TextField(blank=True, help_text="YAML vars for storage configuration")
    configuration_settings = models.TextField(blank=False, help_text=(
        'A record of the combined (final) ansible variables passed to the configuration '
        'playbook when configuring this AppServer.'
    ))

    CONFIGURATION_PLAYBOOK = 'edx_sandbox'
    CONFIGURATION_VARS_TEMPLATE = 'instance/ansible/vars.yml'
    # Additional model fields/properties that contain yaml vars to add the the configuration vars:
    CONFIGURATION_EXTRA_FIELDS = [
        'configuration_database_settings',
        'configuration_storage_settings',
        'configuration_extra_settings',
    ]

    class Meta:
        verbose_name = 'Open edX App Server'

    def set_field_defaults(self):
        """
        Set default values.
        """
        # Always override configuration_settings - it's not meant to be manually set. We can't
        # assert that it isn't set because if a ValidationError occurred, this method could be
        # called multiple times before this AppServer is successfully created.
        self.configuration_settings = self.create_configuration_settings()
        super().set_field_defaults()

    def get_playbooks(self):
        """
        Get the ansible playbooks used to provision this AppServer
        """
        return super().get_playbooks() + [
            Playbook(
                source_repo=self.configuration_source_repo_url,
                requirements_path='requirements.txt',
                playbook_path='playbooks/{}.yml'.format(self.CONFIGURATION_PLAYBOOK),
                version=self.configuration_version,
                variables=self.configuration_settings,
            )
        ]

    def create_configuration_settings(self):
        """
        Generate the configuration settings.

        This is a one-time thing, because configuration_settings, like all AppServer fields, is
        immutable once this AppServer is saved.
        """
        template = loader.get_template(self.CONFIGURATION_VARS_TEMPLATE)
        vars_str = template.render({
            'appserver': self,
            'instance': self.instance,
            # This property is needed twice in the template.  To avoid evaluating it twice (and
            # querying the Github API twice), we pass it as a context variable.
            'github_admin_username_list': self.github_admin_username_list,
        })
        for attr_name in self.CONFIGURATION_EXTRA_FIELDS:
            additional_vars = getattr(self, attr_name)
            vars_str = ansible.yaml_merge(vars_str, additional_vars)
        self.logger.debug('Vars.yml:\n%s', vars_str)
        return vars_str

    @property
    def github_admin_username_list(self):
        """
        Returns the github usernames of this instance admins

        Admins are the members of the default team of the `github_admin_organization_name` org
        """
        if self.github_admin_organization_name:
            return get_username_list_from_team(self.github_admin_organization_name)
        else:
            return []

    @log_exception
    @AppServer.status.only_for(AppServer.Status.New)
    def provision(self):
        """
        Provision this AppServer.

        Returns True on success or False on failure
        """
        self.logger.info('Starting provisioning')
        # Start by requesting a new server/VM:
        self._status_to_waiting_for_server()
        assert self.server.vm_not_yet_requested
        self.server.name_prefix = ('edxapp-' + slugify(self.instance.sub_domain))[:20]
        self.server.save()

        def accepts_ssh_commands():
            """ Does server accept SSH commands? """
            return self.server.status.accepts_ssh_commands

        try:
            self.server.start()
            self.logger.info('Waiting for server %s...', self.server)
            self.server.sleep_until(lambda: self.server.status.vm_available)
            self.logger.info('Waiting for server %s to finish booting...', self.server)
            self.server.sleep_until(accepts_ssh_commands)
        except:  # pylint: disable=bare-except
            self._status_to_error()
            message = 'Unable to start an OpenStack server'
            self.logger.exception(message)
            self.provision_failed_email(message)
            return False

        try:
            # Provisioning (ansible)
            self.logger.info('Provisioning server...')
            self._status_to_configuring_server()
            log, exit_code = self.run_ansible_playbooks()
            if exit_code != 0:
                self.logger.info('Provisioning failed')
                self._status_to_configuration_failed()
                self.provision_failed_email("AppServer deploy failed: Ansible play exited with non-zero exit code", log)
                return False

            # Reboot
            self.logger.info('Provisioning completed')
            self.logger.info('Rebooting server %s...', self.server)
            self.server.reboot()
            self.server.sleep_until(accepts_ssh_commands)

            # Declare instance up and running
            self._status_to_running()

            return True

        except:  # pylint: disable=bare-except
            self._status_to_configuration_failed()
            message = "AppServer deploy failed: unhandled exception"
            self.logger.exception(message)
            self.provision_failed_email(message)
            return False

    @staticmethod
    def on_post_save(sender, instance, created, **kwargs):
        """
        Called when an OpenEdXAppServer is saved.
        """
        publish_data('notification', {
            'type': 'openedx_appserver_update',
            'appserver_id': instance.pk,
            'instance_id': instance.owner.pk,  # This is the ID of the InstanceReference
        })

post_save.connect(OpenEdXAppServer.on_post_save, sender=OpenEdXAppServer)
