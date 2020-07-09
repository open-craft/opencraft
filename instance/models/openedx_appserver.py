# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
import os
import yaml

import requests

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from django.utils.text import slugify
from django.contrib.postgres.fields import JSONField

from instance import ansible
from instance.logging import log_exception
from instance.models.appserver import AppServer
from instance.models.mixins.ansible import AnsibleAppServerMixin, Playbook
from instance.models.mixins.utilities import EmailMixin
from instance.models.mixins.openedx_config import OpenEdXConfigMixin
from instance.models.utils import default_setting, format_help_text, get_base_playbook_name
from instance.openstack_utils import get_openstack_connection, sync_security_group_rules, SecurityGroupRuleDefinition
from instance.utils import publish_data
from userprofile.models import UserProfile

# Constants ###################################################################


# OpenStack firewall rules (security group rules) to apply to the main security group of each AppServer:
OPENEDX_APPSERVER_SECURITY_GROUP_RULES = [
    # Convert this setting from a list of dicts to a list of SecurityGroupRuleDefinition tuples.
    SecurityGroupRuleDefinition(**rule) for rule in settings.OPENEDX_APPSERVER_SECURITY_GROUP_RULES
]


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
    privacy_policy_url = models.URLField(
        verbose_name='URL to Privacy Policy',
        help_text=('URL to the privacy policy.'),
        blank=True,
        default='',
    )

    openedx_release = models.CharField(
        max_length=128,
        blank=False,
        default=default_setting('DEFAULT_OPENEDX_RELEASE'),
        help_text=format_help_text(
            """
            Set this to a release tag like "named-release/dogwood" to build a specific release of
            Open edX. This setting becomes the default value for edx_platform_version,
            forum_version, notifier_version, xqueue_version, and certs_version so it should be a git
            branch that exists in all of those repositories.

            Note: to build a specific branch of edx-platform, you should just override
            edx_platform_commit rather than changing this setting.

            Note 2: This value does not affect the default value of configuration_version.
            """
        ),
    )

    # Ansible-specific settings:
    configuration_source_repo_url = models.URLField(
        max_length=256,
        blank=False,
        default=default_setting('DEFAULT_CONFIGURATION_REPO_URL'),
    )
    configuration_version = models.CharField(
        max_length=50,
        blank=False,
        default=default_setting('DEFAULT_CONFIGURATION_VERSION'),
    )
    configuration_extra_settings = models.TextField(blank=True, help_text="YAML config vars that override all others")
    configuration_playbook_name = models.CharField(
        max_length=100,
        blank=True,
    )

    edx_platform_repository_url = models.CharField(
        max_length=256,
        blank=False,
        default=default_setting('DEFAULT_EDX_PLATFORM_REPO_URL'),
        help_text=(
            'URL to the edx-platform repository to use. Leave blank for default.'
        ),
    )
    edx_platform_commit = models.CharField(max_length=256, blank=False, help_text=(
        'edx-platform commit hash or branch or tag to use. Leave blank to use the default, '
        'which is equal to the value of "openedx_release".'
    ))

    # OpenStack VM settings
    openstack_server_flavor = JSONField(
        null=True,
        blank=True,
        default=default_setting('OPENSTACK_SANDBOX_FLAVOR'),
        help_text='JSON openstack flavor selector, e.g. {"name": "vps-ssd-1"}.'
                  ' Defaults to settings.OPENSTACK_SANDBOX_FLAVOR on server creation.',
    )
    openstack_server_base_image = JSONField(
        null=True,
        blank=True,
        default=default_setting('OPENSTACK_SANDBOX_BASE_IMAGE'),
        help_text='JSON openstack base image selector, e.g. {"name": "xenial-16.04-unmodified"}'
                  ' Defaults to settings.OPENSTACK_SANDBOX_BASE_IMAGE on server creation.',
    )
    openstack_server_ssh_keyname = models.CharField(
        max_length=256,
        null=True,
        blank=True,
        default=default_setting('OPENSTACK_SANDBOX_SSH_KEYNAME'),
        help_text='SSH key name used when setting up access to the openstack project.'
                  ' Defaults to settings.OPENSTACK_SANDBOX_SSH_KEYNAME on server creation.',
    )

    # Misc settings:
    lms_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        help_text='Instance manager users that should be made staff users on the instance.',
    )
    additional_security_groups = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True,
        help_text=(
            "Optional: A list of extra OpenStack security group names to use for this instance's VMs. "
            "A typical use case is to grant this instance access to a private database server that is "
            "behind a firewall. (In the django admin, separate group names with a comma.)"
        )
    )
    additional_monitoring_emails = ArrayField(
        models.CharField(max_length=200),
        default=list,
        blank=True,
        help_text=(
            "Optional: A list of additional email addresses other than settings.ADMINS "
            "who should receive alerts from New Relic Synthetics Monitors when this instance "
            "becomes unavailable."
        )
    )
    provisioning_failure_notification_emails = ArrayField(  # pylint: disable=invalid-name
        models.CharField(max_length=200),
        default=list,
        blank=True,
        help_text=(
            "Optional: A list of additional email addresses other than settings.ADMINS "
            "who should receive alerts when an AppServer fails to provision."
        )
    )
    openedx_appserver_count = models.IntegerField(
        default=1,
        help_text=(
            "The number of Open edX AppServers to deploy for this instance."
        )
    )

    @property
    def public_contact_email(self):
        """ Helper to provide similar API to get email as BetaTestApplication """
        return self.email

    @property
    def base_playbook_name(self):
        """
        Get the correct base playbook name for the openedx_release

        Automatically fills the field if left empty
        """
        if not self.configuration_playbook_name:
            self.configuration_playbook_name = get_base_playbook_name(self.openedx_release)
            self.save()
        return self.configuration_playbook_name

    @classmethod
    def get_config_fields(cls):
        """
        Get the names of each field declared on this model (except the automatic ID field).

        This is used to copy the current values from an Instance to an AppServer when creating
        a new AppServer.
        """
        return [field.name for field in cls._meta.fields if field.name not in ('id', )]


class OpenEdXAppServer(AppServer, OpenEdXAppConfiguration, AnsibleAppServerMixin, OpenEdXConfigMixin, EmailMixin):
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
    configuration_theme_settings = models.TextField(blank=True, help_text="YAML vars for theme configuration")
    configuration_site_configuration_settings = models.TextField(  # pylint:disable=invalid-name
        blank=True, null=True, help_text="YAML vars for setting SiteConfiguration variables"
    )
    configuration_secret_keys = models.TextField(blank=True, help_text="YAML vars for secret keys")
    configuration_settings = models.TextField(blank=False, help_text=(
        'A record of the combined (final) ansible variables passed to the configuration '
        'playbook when configuring this AppServer.'
    ))
    lms_user_settings = models.TextField(blank=True, help_text='YAML variables for LMS user creation.')

    INVENTORY_GROUP = 'openedx-app'

    MANAGE_USERS_PLAYBOOK = 'playbooks/edx-east/manage_edxapp_users_and_groups.yml'

    # Additional model fields/properties that contain yaml vars to add the the configuration vars:
    CONFIGURATION_EXTRA_FIELDS = [
        'configuration_database_settings',
        'configuration_storage_settings',
        'configuration_theme_settings',
        'configuration_site_configuration_settings',
        'configuration_secret_keys',
        # The extra settings should stay at the end of this list to allow manual overrides of all settings.
        'configuration_extra_settings',
    ]

    class Meta(AppServer.Meta):
        verbose_name = 'Open edX App Server'

    def make_active(self, active=True):
        """
        Activate or deactivate the current appserver.
        Reconfigure the load balancer, and if activating, enable monitoring.

        Parameters:
        * `active`: defaults to True.  Set to False to deactivate the appserver.
        """
        self.logger.info(
            'Making %s %s for instance %s...',
            self.name,
            "active" if active else "inactive",
            self.instance.name
        )
        # Try to start/stop services on VM.
        # If this fails, block instance activation/deactivation
        if not self.manage_instance_services(active=active):
            self.logger.error(
                'Failed to start/stop Open edX services on instance %s...',
                self.instance.name
            )
            # Allow deactivating failing appservers but block activating
            # appserver when the playbook fails
            if active:
                return

            self.logger.info(
                "Allowing appserver %s to be stopped since it's being deactivated.",
                self.instance.name
            )

        self.is_active = active
        self.save()
        self.instance.reconfigure_load_balancer()
        if active:
            self.instance.enable_monitoring()
        self.instance.set_active_vm_dns_records(deactivate_appserver=not active)
        self.instance.update_consul_metadata()

    @AppServer.status.only_for(AppServer.Status.New)
    def add_lms_users(self, lms_users):
        """
        Add local Django users to the list of LMS users to be created on the instance.
        """
        self.lms_users.add(*lms_users)
        self.lms_user_settings = self.create_lms_user_settings()
        self.save()

    def default_playbook(self):
        """
        Return a Playbook instance for the standard configuration playbook.
        """
        return Playbook(
            source_repo=self.configuration_source_repo_url,
            requirements_path='requirements.txt',
            playbook_path=self.base_playbook_name,
            version=self.configuration_version,
            variables=self.configuration_settings,
        )

    def lms_user_creation_playbook(self):
        """
        Return a Playbook instance for creating LMS users.
        """
        return Playbook(
            source_repo=self.configuration_source_repo_url,
            requirements_path='requirements.txt',
            playbook_path=self.MANAGE_USERS_PLAYBOOK,
            version=self.configuration_version,
            variables=self.lms_user_settings,
        )

    def manage_services_playbook(self, action, services="edxapp_worker:"):
        """
        Return a Playbook instance for creating LMS users.
        """
        playbook_settings = yaml.dump(
            {
                "supervisord_action": action,
                "services": services,
            },
            default_flow_style=False
        )

        return Playbook(
            version=None,
            source_repo=os.path.join(settings.SITE_ROOT, 'playbooks/manage_services'),
            requirements_path='requirements.txt',
            playbook_path='manage_services.yml',
            variables=playbook_settings,
        )

    def enable_bulk_emails_playbook(self):
        """
        Return a Playbook instance for enabling the Bulk Email feature.
        """
        return Playbook(
            version=None,
            source_repo=os.path.join(settings.SITE_ROOT, 'playbooks/enable_bulk_emails'),
            requirements_path='requirements.txt',
            playbook_path='enable_bulk_emails.yml',
            variables='{}',
        )

    def get_playbooks(self):
        """
        Get the ansible playbooks used to provision this AppServer
        """
        playbooks = [self.default_playbook()]
        if self.lms_users.count():
            playbooks.append(self.lms_user_creation_playbook())
        if not self.instance.successfully_provisioned:
            playbooks.append(self.enable_bulk_emails_playbook())
        return playbooks + super().get_playbooks()

    def create_configuration_settings(self):
        """
        Generate the configuration settings.

        This is a one-time thing, because configuration_settings, like all AppServer fields, is
        immutable once this AppServer is saved.
        """
        confvars = self._get_configuration_variables()
        for attr_name in self.CONFIGURATION_EXTRA_FIELDS:
            additional_vars = getattr(self, attr_name)
            additional_vars = yaml.load(additional_vars, Loader=yaml.SafeLoader) if additional_vars else {}
            confvars = ansible.dict_merge(confvars, additional_vars)
        vars_str = yaml.dump(confvars, default_flow_style=False)
        self.logger.debug('Vars.yml:\n%s', vars_str)
        return vars_str

    def create_lms_user_settings(self):
        """
        Generate the settings for creating the initial LMS users.
        """
        return yaml.dump(
            {
                "EDXAPP_SETTINGS": 'openstack',
                "django_users": [
                    {
                        "email": user.email,
                        "username": user.username,
                        "initial_password_hash": user.password,
                        "staff": True,
                        "superuser": True
                    }
                    for user in self.lms_users.all()
                ],
                "django_groups": [],
                # We do not require users to be created successfully if we have
                # successfully provisioned any app servers for this instance in the past;
                # we assume we got it right the first time and don't worry about errors.
                "ignore_user_creation_errors": not self.instance.require_user_creation_success()
            },
            default_flow_style=False
        )

    @property
    def smtp_relay_settings(self):
        """
        If external SMTP relay is configured, return a dictionary of settings to be consumed by postfix_queue role.
        If external SMTP relay is not configured, return None.
        """
        if settings.INSTANCE_SMTP_RELAY_HOST:
            return {
                'host': settings.INSTANCE_SMTP_RELAY_HOST,
                'port': settings.INSTANCE_SMTP_RELAY_PORT,
                'username': settings.INSTANCE_SMTP_RELAY_USERNAME,
                'password': settings.INSTANCE_SMTP_RELAY_PASSWORD,
                # edX sometimes constructs course-specific email addresses by prefixing the course slug.
                # (for example: info@example.com -> DemoX-info@example.com).
                # In order to properly rewrite all emails sent from edX, use a wildcard "@domain.com" source address.
                'source_address': '@{}'.format(self.email.split('@')[-1]),
                'rewritten_address': '{}@{}'.format(self.instance.domain, settings.INSTANCE_SMTP_RELAY_SENDER_DOMAIN),
            }
        else:
            return None

    @property
    def admin_users(self):
        """
        Retrieve all users that fulfill requirements defined via `admin_user_query`,
        excluding any users that don't have a meaningful GitHub username.
        (Without a meaningful GitHub username it won't be possible
        to correctly set up SSH access to a given sandbox.)

        Admins are all users with `is_superuser` set to `True`,
        as well as all members of the organization that owns this instance.

        :return: GitHub usernames, if exists, of admin users for this instance.
        """
        admin_user_query = Q(user__is_superuser=True)

        # Add members of owning organization to the list of users that can administer this instance
        organization = self.instance.ref.owner
        if organization:
            admin_user_query = admin_user_query | Q(organization=organization)

        users = UserProfile.objects \
            .filter(admin_user_query) \
            .filter(user__is_active=True) \
            .exclude(Q(github_username__isnull=True) | Q(github_username__exact='')) \
            .values_list('github_username', flat=True)

        return list(users)

    @property
    def security_groups(self):
        """
        List of the names of each OpenStack network security group used by this
        AppServer

        Example return value: ["edxapp-appserver"]
        """
        return [settings.OPENEDX_APPSERVER_SECURITY_GROUP_NAME] + self.additional_security_groups

    def check_security_groups(self):
        """
        For security reasons, every edxapp AppServer should be in a security
        group that only allows access to a few ports, like 443 and 22.

        The security group with the name specified by
        settings.OPENEDX_APPSERVER_SECURITY_GROUP_NAME is created and managed
        by this code.
        """
        self.logger.info('Checking security groups (OpenStack firewall settings)')
        network = get_openstack_connection(self.instance.openstack_region).network
        main_security_group = network.find_security_group(settings.OPENEDX_APPSERVER_SECURITY_GROUP_NAME)
        if not main_security_group:
            # We need to create this security group:
            main_security_group = network.create_security_group(name=settings.OPENEDX_APPSERVER_SECURITY_GROUP_NAME)
        description = 'Security group for Open EdX AppServers. Managed automatically by OpenCraft IM.'
        if main_security_group.description != description:
            network.update_security_group(main_security_group, description=description)

        # We manage this security group - update its rules to match the configured list of rules
        sync_security_group_rules(main_security_group, OPENEDX_APPSERVER_SECURITY_GROUP_RULES, network=network)

        # For any additional security groups, just verify that the group exists:
        groups = self.security_groups
        groups.remove(main_security_group.name) # We already checked this group
        for group_name in groups:
            if network.find_security_group(group_name) is None:
                raise Exception("Unable to find the OpenStack network security group called '{}'.".format(group_name))

    @property
    def server_name_prefix(self):
        """
        Prefix for the associated server name.
        """
        return ('edxapp-' + slugify(self.instance.domain))[:20]

    @property
    def server_hostname(self):
        """
        Hostname value for the associated server.
        """
        return '{}-{}'.format(self.server_name_prefix, slugify(self.name))

    def heartbeat_active(self):
        """Is this server's /heartbeat running ok (returning code < 400)"""
        try:
            return requests.options('http://{}/heartbeat'.format(self.server.public_ip)).ok
        except requests.exceptions.ConnectionError:
            return False

    @log_exception
    @AppServer.status.only_for(AppServer.Status.New)
    def provision(self):
        """
        Provision this AppServer.

        Returns True on success or False on failure
        """
        self.logger.info('Starting provisioning')

        # Check firewall rules:
        try:
            self.check_security_groups()
        except:  # pylint: disable=bare-except
            message = "Unable to check/update the network security groups for the new VM"
            self.logger.exception(message)
            self.provision_failed_email(message)
            return False

        # Requesting a new server/VM:
        self._status_to_waiting_for_server()
        assert self.server.vm_not_yet_requested
        self.server.name_prefix = self.server_name_prefix
        self.server.save()

        def accepts_ssh_commands():
            """ Does server accept SSH commands? """
            return self.server.status.accepts_ssh_commands

        try:
            self.server.start(
                security_groups=self.security_groups,
                flavor_selector=self.openstack_server_flavor,
                image_selector=self.openstack_server_base_image,
                key_name=self.openstack_server_ssh_keyname,
            )
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
            self.server.sleep_until(self.heartbeat_active, steady_state_check=False, timeout=1800)

            # Declare instance up and running
            self._status_to_running()

            return True

        except:  # pylint: disable=bare-except
            self._status_to_configuration_failed()
            message = "AppServer deploy failed: unhandled exception"
            self.logger.exception(message)
            self.provision_failed_email(message)
            return False

    def manage_instance_services(self, active):
        """
        Manage services on appserver.

        This function can start/stop services on the appserver. This is
        used to stop edxapp services and prevent inactive appservers from
        taking tasks from the celery queues.
        """
        if active:
            action = 'started'
        else:
            action = 'stopped'

        playbook = self.manage_services_playbook(action=action)
        _, returncode = self._run_playbook(
            working_dir=playbook.source_repo,
            playbook=playbook
        )

        if returncode != 0:
            self.logger.error('Playbook failed for AppServer %s', self)
            return False

        self.logger.info('Playbook completed for AppServer %s', self)
        return True

    def terminate_vm(self):
        if self.is_active:
            self.make_active(active=False)
        super().terminate_vm()

    def save(self, *args, **kwargs):  # pylint: disable=arguments-differ
        """
        Save this OpenEdXAppServer
        """
        # Always override configuration_settings - it's not meant to be manually set. We can't
        # assert that it isn't set because if a ValidationError occurred, this method could be
        # called multiple times before this AppServer is successfully created.
        if not self.pk:
            self.configuration_settings = self.create_configuration_settings()
        super().save(*args, **kwargs)
        publish_data({
            'type': 'openedx_appserver_update',
            'appserver_id': self.pk,
            'instance_id': self.owner.pk,
        })
