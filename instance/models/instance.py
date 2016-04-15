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
Instance app models - Instance
"""

# Imports #####################################################################

import logging
import string

from django.conf import settings
from django.db import models
from django.db.backends.utils import truncate_name
from django.template import loader
from django.utils import timezone
from django.utils.crypto import get_random_string
from django_extensions.db.models import TimeStampedModel
from functools import partial

from instance.gandi import GandiAPI
from instance.logger_adapter import InstanceLoggerAdapter
from instance.logging import log_exception
from instance.models.mixins.ansible import AnsibleInstanceMixin
from instance.models.mixins.database import MongoDBInstanceMixin, MySQLInstanceMixin, SwiftContainerInstanceMixin
from instance.models.mixins.utilities import EmailInstanceMixin
from instance.models.mixins.version_control import GitHubInstanceMixin
from instance.models.utils import ValidateModelMixin

# Constants ###################################################################

PROTOCOL_CHOICES = (
    ('http', 'HTTP - Unencrypted clear text'),
    ('https', 'HTTPS - Encrypted'),
)

gandi = GandiAPI()


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Exceptions ##################################################################

class InconsistentInstanceState(Exception):
    """
    Indicates that the status of an instance can't be determined
    """
    pass

# Models ######################################################################


class Instance(ValidateModelMixin, TimeStampedModel):
    """
    Instance - Group of servers running an application made of multiple services
    """
    sub_domain = models.CharField(max_length=50)
    email = models.EmailField(default='contact@example.com')
    name = models.CharField(max_length=250)

    base_domain = models.CharField(max_length=50, blank=True)
    protocol = models.CharField(max_length=5, default='http', choices=PROTOCOL_CHOICES)

    last_provisioning_started = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        unique_together = ('base_domain', 'sub_domain')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.logger = InstanceLoggerAdapter(logger, {'obj': self})

    def __str__(self):
        return '{0.name} ({0.url})'.format(self)

    @property
    def domain(self):
        """
        Instance domain name
        """
        return '{0.sub_domain}.{0.base_domain}'.format(self)

    @property
    def url(self):
        """
        Instance URL
        """
        return u'{0.protocol}://{0.domain}/'.format(self)

    @property
    def active_server_set(self):
        """
        Returns the subset of `self.server_set` which aren't terminated
        """
        return self.server_set.exclude_terminated()

    @property
    def _current_server(self):
        """
        Current active server. Raises InconsistentInstanceState if more than
        one exists.
        """
        active_server_set = self.active_server_set
        if not active_server_set:
            return
        elif active_server_set.count() > 1:
            raise InconsistentInstanceState('Multiple servers are active, which is unsupported')
        else:
            return active_server_set[0]

    @property
    def status(self):
        """
        Instance status
        """
        server = self._current_server
        if server:
            return server.status
        return None

    @property
    def progress(self):
        """
        Instance's current status progress
        """
        server = self._current_server
        if server:
            return server.progress
        return None

    @property
    def event_context(self):
        """
        Context dictionary to include in events
        """
        return {'instance_id': self.pk}

    def save(self, **kwargs):
        """
        Set default values before saving the instance.
        """
        # Set default field values from settings - using the `default` field attribute confuses
        # automatically generated migrations, generating a new one when settings don't match
        if not self.base_domain:
            self.base_domain = settings.INSTANCES_BASE_DOMAIN
        super().save(**kwargs)

    @staticmethod
    def _sort_log_entries(server_logs, instance_logs):
        """
        Helper method to combine the instance and server log outputs in chronological order
        """
        next_server_log_entry = partial(next, server_logs, None)
        next_instance_log_entry = partial(next, instance_logs, None)

        log = []
        instance_log_entry = next_instance_log_entry()
        server_log_entry = next_server_log_entry()

        while instance_log_entry is not None and server_log_entry is not None:
            if server_log_entry.created < instance_log_entry.created:
                log.append(server_log_entry)
                server_log_entry = next_server_log_entry()
            else:
                log.append(instance_log_entry)
                instance_log_entry = next_instance_log_entry()

        while instance_log_entry is not None:
            log.append(instance_log_entry)
            instance_log_entry = next_instance_log_entry()

        while server_log_entry is not None:
            log.append(server_log_entry)
            server_log_entry = next_server_log_entry()

        return log

    def _get_log_entries(self, level_list=None, limit=None):
        """
        Return the list of log entry instances for the instance and its current active server,
        optionally filtering by logging level. If a limit is given, only the latest records are
        returned.
        """
        # TODO: Filter out log entries for which the user doesn't have view rights
        server_log_entry_set = self._current_server.log_entry_set
        if level_list:
            server_log_entry_set = server_log_entry_set.filter(level__in=level_list)
        server_log_entry_set = server_log_entry_set.order_by('pk')
        if limit:
            server_log_entry_set = reversed(server_log_entry_set.reverse()[:limit])
        else:
            server_log_entry_set = server_log_entry_set.iterator()

        instance_log_entry_set = self.log_entry_set
        if level_list:
            instance_log_entry_set = instance_log_entry_set.filter(level__in=level_list)
        instance_log_entry_set = instance_log_entry_set.order_by('pk')
        if limit:
            instance_log_entry_set = reversed(instance_log_entry_set.reverse()[:limit])
        else:
            instance_log_entry_set = instance_log_entry_set.iterator()

        entries = self._sort_log_entries(server_log_entry_set, instance_log_entry_set)
        if limit:
            return entries[-limit:]
        return entries

    @property
    def log_entries(self):
        """
        Return the list of log entry instances for the instance and its current active server
        """
        return self._get_log_entries(limit=settings.LOG_LIMIT)

    @property
    def log_error_entries(self):
        """
        Return the list of error or critical log entry instances for the instance and its current
        active server
        """
        return self._get_log_entries(level_list=['ERROR', 'CRITICAL'])


# pylint: disable=too-many-instance-attributes
class OpenEdXInstance(MySQLInstanceMixin, MongoDBInstanceMixin, SwiftContainerInstanceMixin,
                      AnsibleInstanceMixin, GitHubInstanceMixin, EmailInstanceMixin, Instance):
    """
    A single instance running a set of Open edX services
    """
    forum_version = models.CharField(max_length=50, default='master')
    notifier_version = models.CharField(max_length=50, default='master')
    xqueue_version = models.CharField(max_length=50, default='master')
    certs_version = models.CharField(max_length=50, default='master')

    s3_access_key = models.CharField(max_length=50, blank=True)
    s3_secret_access_key = models.CharField(max_length=50, blank=True)
    s3_bucket_name = models.CharField(max_length=50, blank=True)

    use_ephemeral_databases = models.BooleanField()

    ANSIBLE_SETTINGS = AnsibleInstanceMixin.ANSIBLE_SETTINGS + [
        'ansible_s3_settings',
        'ansible_mysql_settings',
        'ansible_mongo_settings',
        'ansible_swift_settings',
    ]

    class ProvisionMessages(object):
        """
        Class holding ProvisionMessages
        """
        PROVISION_EXCEPTION = u"Instance provision failed due to unhandled exception"
        PROVISION_ERROR = u"Instance deploy method returned non-zero exit code - provision failed"

    class Meta:
        verbose_name = 'Open edX Instance'
        ordering = ['-created']

    @property
    def default_fork(self):
        """
        Name of the fork to use by default, when no repository is specified
        """
        return settings.DEFAULT_FORK

    @property
    def ansible_s3_settings(self):
        """
        Ansible settings for the S3 bucket
        """
        if not self.s3_access_key or not self.s3_secret_access_key or not self.s3_bucket_name:
            return ''

        template = loader.get_template('instance/ansible/s3.yml')
        return template.render({'instance': self})

    @property
    def ansible_mysql_settings(self):
        """
        Ansible settings for the external mysql database
        """
        if self.use_ephemeral_databases or not settings.INSTANCE_MYSQL_URL_OBJ:
            return ''

        template = loader.get_template('instance/ansible/mysql.yml')
        return template.render({'user': self.mysql_user,
                                'pass': self.mysql_pass,
                                'host': settings.INSTANCE_MYSQL_URL_OBJ.hostname,
                                'port': settings.INSTANCE_MYSQL_URL_OBJ.port or 3306,
                                'database': self.mysql_database_name})

    @property
    def ansible_mongo_settings(self):
        """
        Ansible settings for the external mongo database
        """
        if self.use_ephemeral_databases or not settings.INSTANCE_MONGO_URL_OBJ:
            return ''

        template = loader.get_template('instance/ansible/mongo.yml')
        return template.render({'user': self.mongo_user,
                                'pass': self.mongo_pass,
                                'host': settings.INSTANCE_MONGO_URL_OBJ.hostname,
                                'port': settings.INSTANCE_MONGO_URL_OBJ.port or 27017,
                                'database': self.mongo_database_name,
                                'forum_database': self.forum_database_name})

    @property
    def ansible_swift_settings(self):
        """
        Ansible settings for Swift access.
        """
        if self.use_ephemeral_databases or not settings.SWIFT_ENABLE:
            return ''

        template = loader.get_template('instance/ansible/swift.yml')
        return template.render({'user': self.swift_openstack_user,
                                'password': self.swift_openstack_password,
                                'tenant': self.swift_openstack_tenant,
                                'auth_url': self.swift_openstack_auth_url,
                                'region': self.swift_openstack_region})

    @property
    def studio_sub_domain(self):
        """
        Studio sub-domain name (eg. 'studio.master')
        """
        return 'studio.{}'.format(self.sub_domain)

    @property
    def studio_domain(self):
        """
        Studio full domain name (eg. 'studio.master.sandbox.opencraft.com')
        """
        return '{0.studio_sub_domain}.{0.base_domain}'.format(self)

    @property
    def studio_url(self):
        """
        Studio URL
        """
        return u'{0.protocol}://{0.studio_domain}/'.format(self)

    @property
    def database_name(self):
        """
        The database name used for external databases. Escape all non-ascii characters and truncate to 64 chars, the
        maximum for mysql
        """
        name = self.domain.replace('.', '_')
        allowed = string.ascii_letters + string.digits + '_'
        escaped = ''.join(char for char in name if char in allowed)
        return truncate_name(escaped, length=64)

    @property
    def mysql_database_name(self):
        """
        The mysql database name for this instance
        """
        return self.database_name

    @property
    def mysql_database_names(self):
        """
        List of mysql database names
        """
        return [self.mysql_database_name]

    @property
    def mongo_database_name(self):
        """
        The name of the main external mongo database
        """
        return self.database_name

    @property
    def forum_database_name(self):
        """
        The name of the external database used for forums
        """
        return '{0}_forum'.format(self.database_name)

    @property
    def mongo_database_names(self):
        """
        List of mongo database names
        """
        return [self.mongo_database_name, self.forum_database_name]

    @property
    def swift_container_name(self):
        """
        The name of the Swift container used by the instance.
        """
        return self.database_name

    @property
    def swift_container_names(self):
        """
        The list of Swift container names to be created.
        """
        return [self.swift_container_name]

    def save(self, **kwargs):
        """
        Set this instance's default field values
        """
        if self.use_ephemeral_databases is None:
            self.use_ephemeral_databases = settings.INSTANCE_EPHEMERAL_DATABASES
        super().save(**kwargs)

    def update_from_pr(self, pr):
        """
        Update this instance with settings from the given pull request
        """
        super().update_from_pr(pr)
        self.ansible_extra_settings = pr.extra_settings
        self.use_ephemeral_databases = pr.use_ephemeral_databases(self.domain)
        self.ansible_source_repo_url = pr.get_extra_setting('edx_ansible_source_repo')
        self.configuration_version = pr.get_extra_setting('configuration_version')

    @log_exception
    def provision(self):
        """
        Run the provisioning sequence of the instance, recreating the servers from scratch

        Returns: (server, log)
        """
        self.last_provisioning_started = timezone.now()

        # Server
        self.logger.info('Terminate servers')
        self.server_set.terminate()
        self.logger.info('Start new server')
        server = self.server_set.create()
        server.start()

        def accepts_ssh_commands():
            """ Does server accept SSH commands? """
            return server.status.accepts_ssh_commands

        try:
            # DNS
            self.logger.info('Waiting for IP assignment on server %s...', server)
            server.sleep_until(accepts_ssh_commands)
            self.logger.info('Updating DNS: LMS at %s...', self.domain)
            gandi.set_dns_record(type='A', name=self.sub_domain, value=server.public_ip)
            self.logger.info('Updating DNS: Studio at %s...', self.studio_domain)
            gandi.set_dns_record(type='CNAME', name=self.studio_sub_domain, value=self.sub_domain)

            # Provisioning (external databases)
            if not self.use_ephemeral_databases:
                self.logger.info('Provisioning MySQL database...')
                self.provision_mysql()
                self.logger.info('Provisioning MongoDB databases...')
                self.provision_mongo()
                self.logger.info('Provisioning Swift container...')
                self.provision_swift()

            # Provisioning (ansible)
            server.mark_as_provisioning()
            self.reset_ansible_settings(commit=True)
            log, exit_code = self.deploy()
            if exit_code != 0:
                server.mark_provisioning_finished(success=False)
                self.provision_failed_email(self.ProvisionMessages.PROVISION_ERROR, log)
                return (server, log)

            server.mark_provisioning_finished(success=True)

            # Reboot
            self.logger.info('Rebooting server %s...', server)
            server.reboot()
            server.sleep_until(accepts_ssh_commands)
            self.logger.info('Provisioning completed')

            return (server, log)

        except:
            self.server_set.terminate()
            self.provision_failed_email(self.ProvisionMessages.PROVISION_EXCEPTION)
            raise

    def provision_mysql(self):
        """
        Set mysql credentials and provision the database.
        """
        if not self.mysql_provisioned:
            self.mysql_user = get_random_string(length=16, allowed_chars=string.ascii_lowercase)
            self.mysql_pass = get_random_string(length=32)
        return super().provision_mysql()

    def provision_mongo(self):
        """
        Set mongo credentials and provision the database.
        """
        if not self.mongo_provisioned:
            self.mongo_user = get_random_string(length=16, allowed_chars=string.ascii_lowercase)
            self.mongo_pass = get_random_string(length=32)
        return super().provision_mongo()

    def provision_swift(self):
        """
        Set Swfit credentials and create the Swift container.
        """
        if settings.SWIFT_ENABLE and not self.swift_provisioned:
            # TODO: Figure out a way to use separate credentials for each instance.  Access control
            # on Swift containers is granted to users, and there doesn't seem to be a way to create
            # Keystone users in OpenStack public clouds.
            self.swift_openstack_user = settings.SWIFT_OPENSTACK_USER
            self.swift_openstack_password = settings.SWIFT_OPENSTACK_PASSWORD
            self.swift_openstack_tenant = settings.SWIFT_OPENSTACK_TENANT
            self.swift_openstack_auth_url = settings.SWIFT_OPENSTACK_AUTH_URL
            self.swift_openstack_region = settings.SWIFT_OPENSTACK_REGION
        return super().provision_swift()
