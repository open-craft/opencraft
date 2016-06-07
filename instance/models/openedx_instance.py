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
Open edX Instance models
"""
import string

from django.conf import settings
from django.db import models, transaction
from django.db.backends.utils import truncate_name
from tldextract import TLDExtract

from instance.gandi import GandiAPI
from instance.logging import log_exception
from .instance import Instance
from .mixins.openedx_database import OpenEdXDatabaseMixin
from .mixins.openedx_monitoring import OpenEdXMonitoringMixin
from .mixins.openedx_storage import OpenEdXStorageMixin
from .openedx_appserver import OpenEdXAppConfiguration, OpenEdXAppServer, DEFAULT_EDX_PLATFORM_REPO_URL

# Constants ###################################################################

gandi = GandiAPI()

# By default, tldextract will make an http request to fetch an updated list of
# TLDs on first invocation. Passing suffix_list_urls=None here prevents this.
tldextract = TLDExtract(suffix_list_urls=None)


# Models ######################################################################

# pylint: disable=too-many-instance-attributes
class OpenEdXInstance(Instance, OpenEdXAppConfiguration, OpenEdXDatabaseMixin,
                      OpenEdXMonitoringMixin, OpenEdXStorageMixin):
    """
    OpenEdXInstance: represents a website or set of affiliated websites powered by the same
    OpenEdX installation.
    """

    # Most settings/fields are inherited from OpenEdXAppConfiguration
    sub_domain = models.CharField(max_length=50)
    base_domain = models.CharField(max_length=50, blank=True)

    active_appserver = models.OneToOneField(
        OpenEdXAppServer, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )

    class Meta:
        unique_together = ('base_domain', 'sub_domain')
        verbose_name = 'Open edX Instance'

    def __str__(self):
        return "{} ({})".format(self.name, self.domain)

    @property
    def domain(self):
        """
        Instance domain name
        """
        return '{0.sub_domain}.{0.base_domain}'.format(self)

    @property
    def url(self):
        """
        LMS URL
        """
        return u'{0.protocol}://{0.domain}/'.format(self)

    @property
    def studio_sub_domain(self):
        """
        Studio sub-domain name (eg. 'studio-master')
        """
        return 'studio-{}'.format(self.sub_domain)

    @property
    def studio_domain(self):
        """
        Studio full domain name (eg. 'studio-master.sandbox.opencraft.com')
        """
        return '{0.studio_sub_domain}.{0.base_domain}'.format(self)

    @property
    def studio_url(self):
        """
        Studio URL
        """
        return u'{0.protocol}://{0.studio_domain}/'.format(self)

    @property
    def lms_preview_sub_domain(self):
        """
        LMS preview sub-domain name (eg. 'preview-master')
        """
        return 'preview-{}'.format(self.sub_domain)

    @property
    def lms_preview_domain(self):
        """
        LMS preview full domain name (eg. 'preview-master.sandbox.opencraft.com')
        """
        return '{0.lms_preview_sub_domain}.{0.base_domain}'.format(self)

    @property
    def lms_preview_url(self):
        """
        LMS preview URL
        """
        return u'{0.protocol}://{0.lms_preview_domain}/'.format(self)

    @property
    def database_name(self):
        """
        The database name used for external databases/storages, if any.
        """
        name = self.domain.replace('.', '_')
        # Escape all non-ascii characters and truncate to 50 chars.
        # The maximum length for the name of a MySQL database is 64 characters.
        # But since we add suffixes to database_name to generate unique database names
        # for different services (e.g. xqueue) we don't want to use the maximum length here.
        allowed = string.ascii_letters + string.digits + '_'
        escaped = ''.join(char for char in name if char in allowed)
        return truncate_name(escaped, length=50)

    def set_field_defaults(self):
        """
        Set default values.
        """
        # Main settings
        if not self.openedx_release:
            self.openedx_release = settings.DEFAULT_OPENEDX_RELEASE
        if not self.configuration_source_repo_url:
            self.configuration_source_repo_url = settings.DEFAULT_CONFIGURATION_REPO_URL
        if not self.configuration_version:
            self.configuration_version = settings.DEFAULT_CONFIGURATION_VERSION
        if not self.edx_platform_repository_url:
            self.edx_platform_repository_url = DEFAULT_EDX_PLATFORM_REPO_URL
        if not self.edx_platform_commit:
            self.edx_platform_commit = self.openedx_release

        # Database settings
        OpenEdXDatabaseMixin.set_field_defaults(self)

        # Storage settings
        OpenEdXStorageMixin.set_field_defaults(self)

        # Other settings
        super().set_field_defaults()

    def save(self, **kwargs):
        """
        Set default values before saving the instance.
        """
        # Set default field values from settings - using the `default` field attribute confuses
        # automatically generated migrations, generating a new one when settings don't match
        if not self.base_domain:
            self.base_domain = settings.DEFAULT_INSTANCE_BASE_DOMAIN
        if self.use_ephemeral_databases is None:
            self.use_ephemeral_databases = settings.INSTANCE_EPHEMERAL_DATABASES
        super().save(**kwargs)

    def delete(self, *args, **kwargs):
        """
        Delete this Open edX Instance and its associated AppServers, and deprovision external databases and storage.
        """
        self.disable_monitoring()
        for appserver in self.appserver_set.all():
            appserver.terminate_vm()
        self.deprovision_mysql()
        self.deprovision_mongo()
        self.deprovision_swift()
        super().delete(*args, **kwargs)

    @property
    def appserver_set(self):
        """
        Get the set of OpenEdxAppServers owned by this instance.
        """
        return self.ref.openedxappserver_set

    def set_appserver_active(self, appserver_id):
        """
        Mark the AppServer with the given ID as the active one.
        """
        app_server = self.appserver_set.get(pk=appserver_id)  # Make sure the AppServer is owned by this instance
        self.logger.info('Making %s active for instance %s...', app_server.name, self.name)
        public_ip = app_server.server.public_ip

        self.logger.info('Updating DNS: LMS at %s...', self.domain)
        lms_domain = tldextract(self.domain)
        gandi.set_dns_record(
            lms_domain.registered_domain,
            type='A', name=lms_domain.subdomain, value=public_ip
        )

        self.logger.info('Updating DNS: LMS preview at %s...', self.lms_preview_domain)
        lms_preview_domain = tldextract(self.lms_preview_domain)
        gandi.set_dns_record(
            lms_preview_domain.registered_domain,
            type='CNAME', name=lms_preview_domain.subdomain, value=lms_domain.subdomain
        )

        self.logger.info('Updating DNS: Studio at %s...', self.studio_domain)
        studio_domain = tldextract(self.studio_domain)
        gandi.set_dns_record(
            studio_domain.registered_domain,
            type='CNAME', name=studio_domain.subdomain, value=lms_domain.subdomain
        )

        self.active_appserver = app_server
        self.save()

        self.enable_monitoring()

    @log_exception
    def spawn_appserver(self):
        """
        Provision a new AppServer.

        Returns the ID of the new AppServer on success or None on failure.
        """
        # Provision external databases:
        if not self.use_ephemeral_databases:
            # TODO: Use db row-level locking to ensure we don't get any race conditions when creating these DBs.
            # Use select_for_update(nowait=True) to lock this object's row, then do these steps, then refresh_from_db
            self.logger.info('Provisioning MySQL database...')
            self.provision_mysql()
            self.logger.info('Provisioning MongoDB databases...')
            self.provision_mongo()
            self.logger.info('Provisioning Swift container...')
            self.provision_swift()

        app_server = self._create_owned_appserver()

        if app_server.provision():
            self.logger.info('Provisioned new app server, %s', app_server.name)
            return app_server.pk
        else:
            self.logger.error('Failed to provision new app server')
            return None

    def _create_owned_appserver(self):
        """
        Core internal code that actually creates the child appserver.

        The only reason this is separated from the public spawn_appserver() method is so that
        tests can use this core code as an AppServer factory.

        This method should never be used directly, except in tests.
        Use spawn_appserver() instead.
        """
        config_fields = OpenEdXAppConfiguration.get_config_fields()
        instance_config = {field_name: getattr(self, field_name) for field_name in config_fields}

        with transaction.atomic():
            app_server = self.appserver_set.create(
                # Name for the app server: this will usually generate a unique name (and won't cause any issues if not):
                name="AppServer {}".format(self.appserver_set.count() + 1),
                # Copy the current value of each setting into the AppServer, preserving it permanently:
                configuration_database_settings=self.get_database_settings(),
                configuration_storage_settings=self.get_storage_settings(),
                **instance_config
            )
            app_server.add_lms_users(self.lms_users.all())
        return app_server
