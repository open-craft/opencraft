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
import re
import string

from django.conf import settings
from django.db import models, transaction
from django.db.backends.utils import truncate_name
from django.template import loader
from tldextract import TLDExtract

from instance.gandi import GandiAPI
from instance.logging import log_exception
from instance.models.appserver import Status as AppServerStatus
from instance.models.server import Status as ServerStatus
from instance.utils import sufficient_time_passed
from .instance import Instance
from .load_balancer import LoadBalancingServer, select_load_balancing_server
from .mixins.openedx_database import OpenEdXDatabaseMixin
from .mixins.openedx_monitoring import OpenEdXMonitoringMixin
from .mixins.openedx_storage import OpenEdXStorageMixin
from .mixins.secret_keys import SecretKeyInstanceMixin
from .openedx_appserver import OpenEdXAppConfiguration, OpenEdXAppServer, DEFAULT_EDX_PLATFORM_REPO_URL

# Constants ###################################################################

gandi = GandiAPI()

# By default, tldextract will make an http request to fetch an updated list of
# TLDs on first invocation. Passing suffix_list_urls=None here prevents this.
tldextract = TLDExtract(suffix_list_urls=None)


# Functions ###################################################################

def generate_internal_lms_domain(sub_domain):
    """
    Generates value for internal_lms_domain field from the supplied sub_domain and the
    DEFAULT_INSTANCE_BASE_DOMAIN setting.
    """
    return '{}.{}'.format(sub_domain, settings.DEFAULT_INSTANCE_BASE_DOMAIN)


# Models ######################################################################

# pylint: disable=too-many-instance-attributes
class OpenEdXInstance(Instance, OpenEdXAppConfiguration, OpenEdXDatabaseMixin,
                      OpenEdXMonitoringMixin, OpenEdXStorageMixin, SecretKeyInstanceMixin):
    """
    OpenEdXInstance: represents a website or set of affiliated websites powered by the same
    OpenEdX installation.
    """

    # Most settings/fields are inherited from OpenEdXAppConfiguration

    # Internal domains are controlled by us and their DNS records are automatically set to point to the current active
    # appserver. They are generated from a unique prefix (given as 'sub_domain' in instance factories) and the value of
    # DEFAULT_INSTANCE_BASE_DOMAIN at instance creation time. They cannot be blank and are normally never changed after
    # the instance is created.
    # External domains on the other hand are controlled by the customer and are optional. We use external domains in
    # preference to internal domains when displaying links to the instance in the UI and when passing domain-related
    # settings to Ansible vars when provisioning appservers.
    # The `domain`, `lms_preview_domain`, and `studio_domain` properties below are useful if you need to access
    # corresponding domains regardless of whether an instance uses external domains or not (they return the external
    # domain if set, and fall back to the corresponding internal domain otherwise).
    internal_lms_domain = models.CharField(max_length=100, blank=False, unique=True)
    internal_lms_preview_domain = models.CharField(max_length=100, blank=False, unique=True)
    internal_studio_domain = models.CharField(max_length=100, blank=False, unique=True)

    external_lms_domain = models.CharField(max_length=100, blank=True)
    external_lms_preview_domain = models.CharField(max_length=100, blank=True)
    external_studio_domain = models.CharField(max_length=100, blank=True)

    load_balancing_server = models.ForeignKey(LoadBalancingServer, null=True, blank=True, on_delete=models.PROTECT)

    active_appserver = models.OneToOneField(
        OpenEdXAppServer, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
    )

    successfully_provisioned = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Open edX Instance'

    def __init__(self, *args, **kwargs):
        """
        OpenEdXInstance constructor.

        The constructor is overridden to optionally accept a 'sub_domain' parameter instead of a full
        value for 'internal_lms_domain'. When 'sub_domain' is provided, the 'internal_lms_domain' field is automatically
        generated from from the value of 'sub_domain' and the DEFAULT_INSTANCE_BASE_DOMAIN setting.
        """
        if 'sub_domain' in kwargs:
            sub_domain = kwargs.pop('sub_domain')
            if 'internal_lms_domain' not in kwargs:
                kwargs['internal_lms_domain'] = generate_internal_lms_domain(sub_domain)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "{} ({})".format(self.name, self.domain)

    @property
    def domain(self):
        """
        LMS domain name.

        Returns external domain if present, otherwise falls back to internal domain.
        """
        if self.external_lms_domain:
            return self.external_lms_domain
        else:
            return self.internal_lms_domain

    @property
    def lms_preview_domain(self):
        """
        LMS preview domain name.

        Returns external preview domain if present, otherwise falls back to internal preview domain.
        """
        if self.external_lms_preview_domain:
            return self.external_lms_preview_domain
        else:
            return self.internal_lms_preview_domain

    @property
    def studio_domain(self):
        """
        Studio domain name.

        Returns external studio domain if present, otherwise falls back to internal studio domain.
        """
        if self.external_studio_domain:
            return self.external_studio_domain
        else:
            return self.internal_studio_domain

    @property
    def studio_domain_nginx_regex(self):
        """
        Regex that matches either the internal or the external Studio URL.

        This is exclusively meant for the Ansible variable CMS_HOSTNAME to configure the nginx
        server_name regex to match the Studio domains.
        """
        if self.external_studio_domain:
            domains = [self.external_studio_domain, self.internal_studio_domain]
        else:
            domains = [self.internal_studio_domain]
        choices = '|'.join(map(re.escape, domains))  # pylint: disable=bad-builtin
        return '~^({})$'.format(choices)

    @property
    def url(self):
        """
        LMS URL.
        """
        return u'{0.protocol}://{0.domain}/'.format(self)

    @property
    def studio_url(self):
        """
        Studio URL.
        """
        return u'{0.protocol}://{0.studio_domain}/'.format(self)

    @property
    def lms_preview_url(self):
        """
        LMS preview URL.
        """
        return u'{0.protocol}://{0.lms_preview_domain}/'.format(self)

    @property
    def database_name(self):
        """
        The database name used for external databases/storages, if any.
        """
        name = self.internal_lms_domain.replace('.', '_')
        # Escape all non-ascii characters and truncate to 50 chars.
        # The maximum length for the name of a MySQL database is 64 characters.
        # But since we add suffixes to database_name to generate unique database names
        # for different services (e.g. xqueue) we don't want to use the maximum length here.
        allowed = string.ascii_letters + string.digits + '_'
        escaped = ''.join(char for char in name if char in allowed)
        return truncate_name(escaped, length=50)

    @property
    def is_shut_down(self):
        """
        Return True if this instance has been shut down, else False.

        An instance has been shut down if monitoring has been turned off
        and each of its app servers has either been terminated
        or failed to provision and the corresponding VM has since been terminated.

        If an instance has no app servers, we assume that it has *not* been shut down.
        This ensures that the GUI lists newly created instances without app servers.
        """
        if self.appserver_set.count() == 0:
            return False

        def appserver_is_shut_down(appserver):
            """
            Return True if `appserver` has been terminated
            or if it failed to provision and the corresponding VM has since been terminated.
            """
            if appserver.status == AppServerStatus.Terminated:
                return True
            configuration_failed = appserver.status == AppServerStatus.ConfigurationFailed
            vm_terminated = appserver.server.status == ServerStatus.Terminated
            return configuration_failed and vm_terminated

        all_appservers_terminated = all(
            appserver_is_shut_down(appserver) for appserver in self.appserver_set.all()
        )
        monitoring_turned_off = self.new_relic_availability_monitors.count() == 0
        return all_appservers_terminated and monitoring_turned_off

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

        # Generate secret base key
        SecretKeyInstanceMixin.set_random_key(self)

        # Other settings
        super().set_field_defaults()

    def save(self, **kwargs):
        """
        Set default values before saving the instance.
        """
        # Set default field values from settings - using the `default` field attribute confuses
        # automatically generated migrations, generating a new one when settings don't match
        if not self.internal_lms_preview_domain:
            self.internal_lms_preview_domain = settings.DEFAULT_LMS_PREVIEW_DOMAIN_PREFIX + self.internal_lms_domain
        if not self.internal_studio_domain:
            self.internal_studio_domain = settings.DEFAULT_STUDIO_DOMAIN_PREFIX + self.internal_lms_domain
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

    def set_dns_records(self):
        """
        Create CNAME records for the domain names of this instance pointing to the load balancer.
        """
        load_balancer_domain = self.load_balancing_server.domain.rstrip(".") + "."

        self.logger.info('Updating DNS: LMS at %s...', self.internal_lms_domain)
        lms_domain = tldextract(self.internal_lms_domain)
        gandi.set_dns_record(
            lms_domain.registered_domain,
            type='CNAME', name=lms_domain.subdomain, value=load_balancer_domain
        )

        self.logger.info('Updating DNS: LMS preview at %s...', self.internal_lms_preview_domain)
        lms_preview_domain = tldextract(self.internal_lms_preview_domain)
        gandi.set_dns_record(
            lms_preview_domain.registered_domain,
            type='CNAME', name=lms_preview_domain.subdomain, value=load_balancer_domain
        )

        self.logger.info('Updating DNS: Studio at %s...', self.internal_studio_domain)
        studio_domain = tldextract(self.internal_studio_domain)
        gandi.set_dns_record(
            studio_domain.registered_domain,
            type='CNAME', name=studio_domain.subdomain, value=load_balancer_domain
        )

    def get_load_balancer_configuration(self):
        """
        Return the haproxy configuration fragment and backend map for this instance.
        """
        if self.active_appserver:
            backend_name = "be-{}".format(self.active_appserver.server.name)
            server_name = "appserver-{}".format(self.pk)
            ip_address = self.active_appserver.server.public_ip
        else:
            backend_name = "be-preliminary-page-{}".format(self.pk)
            server_name = "preliminary-page"
            ip_address = settings.PRELIMINARY_PAGE_SERVER_IP
        if not ip_address:
            # No active appserver and PRELIMINARY_PAGE_SERVER_IP not set, so there is no backend
            # we can configure.  Simply return an empty configuration in this case.
            self.logger.info("PRELIMINARY_PAGE_SERVER_IP is unset, so not configuring a preliminary backend.")
            return "", ""
        template = loader.get_template("instance/haproxy/backend.conf")
        config = template.render(dict(
            domain=self.domain,
            backend_name=backend_name,
            server_name=server_name,
            ip_address=ip_address,
        ))
        domain_names = [
            self.external_lms_domain, self.external_lms_preview_domain, self.external_studio_domain,
            self.internal_lms_domain, self.internal_lms_preview_domain, self.internal_studio_domain,
        ]
        backend_map = "\n".join(" ".join([domain, backend_name]) for domain in domain_names if domain)
        return backend_map, config

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
        self.active_appserver = app_server
        self.save()
        self.load_balancing_server.reconfigure()
        self.enable_monitoring()

    def set_appserver_inactive(self):
        """
        Reset the active AppServer to None.  Called when the active appserver is terminated.
        """
        self.disable_monitoring()
        self.active_appserver = None
        self.save()
        self.load_balancing_server.reconfigure()

    @log_exception
    def spawn_appserver(self):
        """
        Provision a new AppServer.

        Returns the ID of the new AppServer on success or None on failure.
        """
        if not self.load_balancing_server:
            self.load_balancing_server = select_load_balancing_server()
            self.load_balancing_server.reconfigure()

        # We unconditionally set the DNS records here, though this would only be strictly needed
        # when the first AppServer is spawned.  However, there is no easy way to tell whether the
        # DNS records have already been successfully set, and it doesn't hurt to alway do it.
        self.set_dns_records()

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
            self.successfully_provisioned = True
            self.save()
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
                configuration_secret_keys=self.get_secret_key_settings(),
                **instance_config
            )
            app_server.add_lms_users(self.lms_users.all())
        return app_server

    def require_user_creation_success(self):
        """
        When provisioning users, we don't want to force incompatible changes (e.g., in email)
        if we've previously provisioned a database with the variables we were interested in initially.
        This method returns false if a) we're using non-ephemeral databases and b) we've provisioned
        an appserver (read: database) for this instance in the past.
        """
        return not self.successfully_provisioned or self.use_ephemeral_databases

    def terminate_obsolete_appservers(self, days=2):
        """
        Terminate app servers that were created (more than) `days`
        before the currently-active app server of this instance.

        Do nothing if this instance doesn't have an active app server.
        """
        active_appserver = self.active_appserver
        if active_appserver:
            for appserver in self.appserver_set.all():
                if sufficient_time_passed(appserver.created, active_appserver.created, days):
                    appserver.terminate_vm()

    def shut_down(self):
        """
        Shut down this instance.

        This process consists of two steps:

        1) Disable New Relic monitors.
        2) Terminate all app servers belonging to this instance.
        """
        self.disable_monitoring()
        for appserver in self.appserver_set.all():
            appserver.terminate_vm()
