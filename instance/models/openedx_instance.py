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
Instance app models - Open edX Instance models
"""
import string

from django.conf import settings
from django.db import models, transaction
from django.db.backends.utils import truncate_name
from django.db.models import F
from django.template import loader
from django.utils import timezone

from instance import gandi
from instance.logging import log_exception
from instance.signals import appserver_spawned
from instance.models.appserver import Status as AppServerStatus
from instance.models.instance import Instance
from instance.models.load_balancer import LoadBalancingServer
from instance.models.mixins.load_balanced import LoadBalancedInstance
from instance.models.mixins.domain_names import DomainNameInstance
from instance.models.mixins.openedx_database import OpenEdXDatabaseMixin
from instance.models.mixins.openedx_monitoring import OpenEdXMonitoringMixin
from instance.models.mixins.openedx_storage import OpenEdXStorageMixin
from instance.models.mixins.openedx_theme import OpenEdXThemeMixin
from instance.models.mixins.secret_keys import SecretKeyInstanceMixin
from instance.models.openedx_appserver import OpenEdXAppConfiguration
from instance.models.utils import WrongStateException, ConsulAgent, get_base_playbook_name
from instance.utils import sufficient_time_passed


# Models ######################################################################


class OpenEdXInstance(
        DomainNameInstance,
        LoadBalancedInstance,
        OpenEdXAppConfiguration,
        OpenEdXDatabaseMixin,
        OpenEdXMonitoringMixin,
        OpenEdXStorageMixin,
        OpenEdXThemeMixin,
        SecretKeyInstanceMixin,
        Instance
):
    """
    OpenEdXInstance: represents a website or set of affiliated websites powered by the same
    OpenEdX installation.
    """

    # Most settings/fields are inherited from mixins

    successfully_provisioned = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        """Init."""
        self.random_prefix = kwargs.pop('random_prefix', None)
        super().__init__(*args, **kwargs)

    class Meta:
        verbose_name = 'Open edX Instance'

    def __str__(self):
        return "{} ({})".format(self.name, self.domain)

    def get_active_appservers(self):
        """
        Returns a queryset containing the active appservers.
        """
        if hasattr(self.ref, '_cached_active_appservers'):
            # A database optimization like prefetch_related() has computed the active
            # appservers for a large number of instances and cached that result on
            # the InstanceReference of each one.
            # (This is used to optimize the /api/v1/instances/ endpoint query for example)
            return self.ref._cached_active_appservers
        return self.appserver_set.filter(_is_active=True)

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

    def save(self, **kwargs):
        """
        Set default values before saving the instance.
        """
        # Set default field values from settings - using the `default` field attribute confuses
        # automatically generated migrations, generating a new one when settings don't match
        if not self.edx_platform_commit:
            self.edx_platform_commit = self.openedx_release
        if self.storage_type is None:
            self.storage_type = settings.INSTANCE_STORAGE_TYPE
        # If left blank, the base playbook name will be automatically selected
        # based on the openedx release
        if not self.configuration_playbook_name:
            self.configuration_playbook_name = get_base_playbook_name(self.openedx_release)

        if self.random_prefix is not None:
            self.mysql_user = self.random_prefix

        super().save(**kwargs)
        self.update_consul_metadata()

    def get_load_balancer_configuration(self, triggered_by_instance=False):
        """
        Return the haproxy configuration fragment and backend map for this instance.

        The triggered_by_instance flag indicates whether the reconfiguration was initiated by this
        instance, in which case we log additional information.
        """
        active_appservers = self.get_active_appservers()
        if not active_appservers.exists():
            return self.get_preliminary_page_config(self.ref.pk)

        # Create the haproxy backend configuration from the list of active appservers
        appserver_vars = []
        for appserver in active_appservers:
            server_name = "appserver-{}".format(appserver.pk)
            if not appserver.server.public_ip:
                self.logger.error(
                    "Active appserver does not have a public IP address. This should not happen. "
                    "Updating internal status to double check."
                )
                appserver.server.update_status()
                if not appserver.server.public_ip:
                    raise WrongStateException("Public IP still not available for active appserver. "
                                              "Canceling reconfiguration process.")

            appserver_vars.append(dict(ip_address=appserver.server.public_ip, name=server_name))

        if len(appserver_vars) == 0:
            self.logger.error(
                "No active appservers found with public IP addresses.  This should not happen. "
                "Deconfiguring the load balancer backend."
            )
            return [], []

        backend_name = "be-{}".format(self.domain_slug)
        template = loader.get_template("instance/haproxy/openedx.conf")
        config = template.render(dict(
            domain=self.domain,
            http_auth_info_base64=self.http_auth_info_base64(),
            appservers=appserver_vars,
            health_check=len(appserver_vars) > 1,
        ))
        backend_map = [(domain, backend_name) for domain in self.get_load_balanced_domains()]
        backend_conf = [(backend_name, config)]

        if self.enable_prefix_domains_redirect:
            redirect_backend_name = "be-redirect-{}".format(self.domain_slug)
            redirect_template = loader.get_template('instance/haproxy/redirect.conf')
            redirect_config = redirect_template.render(dict(
                domain=self.internal_lms_domain
            ))
            backend_map += [(domain, redirect_backend_name) for domain in self.get_prefix_domain_names()]
            backend_conf += [(redirect_backend_name, redirect_config)]

        if triggered_by_instance:
            self.logger.info(
                "New load-balancer configuration:\n    backend map: %s\n   configuration: %s",
                backend_map,
                backend_conf,
            )
        return backend_map, backend_conf

    def set_active_vm_dns_records(self):
        """
        Set DNS A records for all active app servers.
        """
        self.logger.info("Setting DNS records for active app servers...")
        for i, appserver in enumerate(self.get_active_appservers(), 1):
            ip_addr = appserver.server.public_ip
            if ip_addr:
                domain = "vm{index}.{base_domain}".format(index=i, base_domain=self.internal_lms_domain)
                gandi.api.set_dns_record(domain, type="A", value=ip_addr)
        # TODO: implement cleaning up DNS addresses that are no longer needed.

    @property
    def appserver_set(self):
        """
        Get the set of OpenEdxAppServers owned by this instance.
        """
        return self.ref.openedxappserver_set

    @property
    def first_activated(self):
        """
        Returns the activation date for the first activated ``AppServer`` for
        this instance, or ``None`` if there is no AppServer, or no AppServer
        has yet been activated.
        :return: Union[None, datetime]
        """
        try:
            first_activated_appserver = self.appserver_set.filter(
                last_activated__isnull=False
            ).earliest('last_activated')
            return first_activated_appserver.last_activated
        except models.ObjectDoesNotExist:
            return

    def _spawn_appserver(self):
        """
            Provision a new AppServer

            Returns the ID of the new AppServer on success or None on failure.
        """
        if not self.load_balancing_server:
            self.load_balancing_server = LoadBalancingServer.objects.select_random()
            self.save()
            self.reconfigure_load_balancer()

        # We unconditionally set the DNS records here, though this would only be strictly needed
        # when the first AppServer is spawned.  However, there is no easy way to tell whether the
        # DNS records have already been successfully set, and it doesn't hurt to always do it.
        self.set_dns_records()

        # Provision external databases:
        # TODO: Use db row-level locking to ensure we don't get any race conditions when creating these DBs.
        # Use select_for_update(nowait=True) to lock this object's row, then do these steps, then refresh_from_db
        self.logger.info('Provisioning MySQL database...')
        self.provision_mysql()
        self.logger.info('Provisioning MongoDB databases...')
        self.provision_mongo()
        if self.storage_type == self.SWIFT_STORAGE:
            self.logger.info('Provisioning Swift container...')
            self.provision_swift()
        elif self.storage_type == self.S3_STORAGE:
            self.logger.info('Provisioning S3 bucket...')
            self.provision_s3()
        self.logger.info('Provisioning RabbitMQ vhost...')
        self.provision_rabbitmq()

        return self._create_owned_appserver()

    @log_exception
    def spawn_appserver(self,
                        mark_active_on_success=False,
                        num_attempts=1,
                        success_tag=None,
                        failure_tag=None):
        """
        Provision a new AppServer

        Wrapper around the spawning function to allow for multiple attempts

        Optionally mark the new AppServer as active when the provisioning completes.
        Optionally retry up to 'num_attempts' times.
        Optionally tag the instance with 'success_tag' when the deployment succeeds,
        or failure_tag if it fails.

        Returns the ID of the new AppServer or None in case of failure.
        """
        for attempt in range(num_attempts):
            self.logger.info("Spawning new AppServer, attempt {} of {}".format(attempt + 1, num_attempts))
            app_server = self._spawn_appserver()

            if app_server and app_server.provision():
                break

            self.logger.error('Failed to provision new app server')

        else:
            self.logger.error('Failed to provision new app server after {} attempts'.format(num_attempts))
            if failure_tag:
                self.tags.add(failure_tag)
            if success_tag:
                self.tags.remove(success_tag)

            # Warn spawn failed after given attempts
            appserver_spawned.send(sender=self.__class__, instance=self, appserver=None)
            return

        self.logger.info('Provisioned new app server, %s', app_server.name)
        self.successfully_provisioned = True
        self.save()

        if failure_tag:
            self.tags.remove(failure_tag)
        if success_tag:
            self.tags.add(success_tag)

        if mark_active_on_success:
            # use task.make_appserver_active to allow disabling others
            app_server.make_active()

        appserver_spawned.send(sender=self.__class__, instance=self, appserver=app_server)

        return app_server.pk

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
                configuration_theme_settings=self.get_theme_settings(),
                configuration_secret_keys=self.get_secret_key_settings(),
                **instance_config
            )
            app_server.add_lms_users(self.lms_users.all())
        return app_server

    def require_user_creation_success(self):
        """
        When provisioning users, we don't want to force incompatible changes (e.g., in email)
        if we've previously provisioned a database with the variables we were interested in initially.
        This method returns false if we've provisioned an appserver (read: database) for this instance
        in the past.
        """
        return not self.successfully_provisioned

    def terminate_obsolete_appservers(self, days=2):
        """
        Terminate app servers that were created more than `days` before now, except:
        - the active appserver(s) if there are any,
        - a release candidate (rc) appserver, to allow testing before the next appserver activation
          (we keep the most recent running appserver)
        - a fallback appserver, for `days` after activating an appserver, to allow reverts
          (we keep the most recent running appserver created before the latest activation)
        """
        latest_active_appserver = None
        if self.get_active_appservers().exists():
            latest_active_appserver = self.get_active_appservers().latest('last_activated')
        fallback_appserver = None
        rc_appserver = None
        now = timezone.now()

        for appserver in self.appserver_set.all().order_by('-created'):
            # Skip active appservers
            if appserver.is_active:
                continue

            # Keep a running appserver as fallback for `days` after latest activation, to allow reverts
            if latest_active_appserver and appserver.created < latest_active_appserver.last_activated:
                if not sufficient_time_passed(latest_active_appserver.last_activated, now, days) \
                        and not fallback_appserver and appserver.status == AppServerStatus.Running:
                    fallback_appserver = appserver
                elif sufficient_time_passed(appserver.created, now, days):
                    appserver.terminate_vm()

            # Keep the most recent running appserver created after activation (or when none is activated)
            # to allow testing of a release candidate (rc)
            else:
                if not rc_appserver and appserver.status == AppServerStatus.Running:
                    rc_appserver = appserver
                elif sufficient_time_passed(appserver.created, now, days):
                    appserver.terminate_vm()

    def archive(self):
        """
        Shut down this instance's app servers, mark it as archived and
        remove its metadata from Consul.
        """
        self.logger.info('Archiving instance started.')
        self.disable_monitoring()
        self.remove_dns_records()
        if self.load_balancing_server is not None:
            load_balancer = self.load_balancing_server
            self.load_balancing_server = None
            self.save()
            self.reconfigure_load_balancer(load_balancer)
        for appserver in self.appserver_set.iterator():
            appserver.terminate_vm()
        self.purge_consul_metadata()
        super().archive()
        self.logger.info('Archiving instance finished.')

    @staticmethod
    def shut_down():
        """
        The shut_down() functionality was replaced with archive() - remind shell users who run this directly.
        """
        raise AttributeError(
            "Use archive() to shut down all of an instances app servers and remove it from the instance list."
        )

    def delete(self, *args, **kwargs):
        """
        Delete this Open edX Instance and its associated AppServers, and deprovision external databases and storage.

        This is handy for development but should not be used in production - just use archive() instead.

        Note:
            There is no boolean flag to ignore Swift or S3 errors
            because when calling `self.deprovision_swfit()` or
            `self.deprovision_s3()` errors are logged but not raised.

        Arguments:
            ignore_errors (bool): Ignore all errors if `True`.
            ignore_mysql_errros (bool): Ignore MySQL errors.
            ignore_mongo_errors (bool): Ignore Mongo errors.
            ignore_rabbitmq_errors (bool): Ignore RabbitMQ errors.
        """
        self.logger.info('Deleting instance: %s.', str(self))

        ignore_errors = kwargs.pop('ignore_errors', False)

        self.archive()
        self.deprovision_mysql(ignore_errors=kwargs.pop('ignore_mysql_errors', ignore_errors))
        self.deprovision_mongo(ignore_errors=kwargs.pop('ignore_mongo_errors', ignore_errors))
        self.deprovision_swift()
        self.deprovision_s3()
        self.deprovision_rabbitmq(ignore_errors=kwargs.pop('ignore_rabbitmq_errors', ignore_errors))

        super().delete(*args, **kwargs)

    @property
    def consul_prefix(self):
        """
        This is a property that helps determining a specific instance's rpefix in
        Consul. The prefix helps in keeping different instances' configurations
        separate from overridings and modifications.

        :return: A unique Key-Value prefix for this instance in Consul.
        """
        return settings.CONSUL_PREFIX.format(ocim=settings.OCIM_ID, instance=self.id)

    def _generate_consul_metadata(self):
        """
        Collects required configurations for this instance to reflect on Consul.
        You can add, delete or alter configurations keys and values here which are
        going to ve reflected in Consul immediately.

        :return: A dict of the configurations.
        """
        active_servers = self.get_active_appservers()
        basic_auth = self.http_auth_info_base64()
        enable_health_checks = active_servers.count() > 1
        active_servers_data = list(active_servers.annotate(public_ip=F('server___public_ip')).values('id', 'public_ip'))
        return {
            'domain_slug': self.domain_slug,
            'domain': self.domain,
            'name': self.name,
            'domains': self.get_load_balanced_domains(),
            'health_checks_enabled': enable_health_checks,
            'basic_auth': basic_auth.decode(),
            'active_app_servers': active_servers_data,
        }

    def _write_metadata_to_consul(self, configurations):
        """
        Reflect passed configurations to Consul.

        If we successfully updated at least one field in Consul
        then the configurations' version number is incremented.

        :note: This still doesn't apply removed-configurations case.
        :param configurations: A dict object contains the configurations
                               to be written on Consul.
        :return: A pair (version, changed) with the current version number and
                 a bool to indicate whether the information was updated.
        """
        return ConsulAgent(prefix=self.consul_prefix).txn_put(configurations)

    def update_consul_metadata(self):
        """
        This method is going over some pre-defined configurations fields
        in this model to reflect their values on Consul.
        If we successfully updated at least one field in Consul
        then the configurations' version number is gonna be incremented.

        :return: A pair (version, changed) with the current version number and
                 a bool to indicate whether the information was updated.
        """
        if not settings.CONSUL_ENABLED:
            return 0, False

        new_configurations = self._generate_consul_metadata()
        version, updated = self._write_metadata_to_consul(new_configurations)
        return version, updated

    def purge_consul_metadata(self):
        """
        This method is responsible for purging all instances' metadata from
        Consul if they exist.
        """
        if not settings.CONSUL_ENABLED:
            return

        self.logger.info('Purging consul metadata with prefix: %s.', self.consul_prefix)
        agent = ConsulAgent(prefix=self.consul_prefix)
        agent.purge()
