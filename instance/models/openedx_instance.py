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
from django.db.models.signals import post_save

from instance.gandi import GandiAPI
from instance.logging import log_exception
from .mixins.openedx_database import OpenEdXDatabaseMixin
from .mixins.openedx_storage import OpenEdXStorageMixin
from .instance import Instance
from .openedx_appserver import OpenEdXAppConfiguration, OpenEdXAppServer

# Constants ###################################################################

gandi = GandiAPI()

# Models ######################################################################


# pylint: disable=too-many-instance-attributes
class OpenEdXInstance(Instance, OpenEdXAppConfiguration, OpenEdXDatabaseMixin, OpenEdXStorageMixin):
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
        The database name used for external databases/storages, if any.
        """
        name = self.domain.replace('.', '_')
        # Escape all non-ascii characters and truncate to 64 chars, the maximum for mysql:
        allowed = string.ascii_letters + string.digits + '_'
        escaped = ''.join(char for char in name if char in allowed)
        return truncate_name(escaped, length=64)

    def save(self, **kwargs):
        """
        Set default values before saving the instance.
        """
        # Set default field values from settings - using the `default` field attribute confuses
        # automatically generated migrations, generating a new one when settings don't match
        if not self.base_domain:
            self.base_domain = settings.INSTANCES_BASE_DOMAIN
        if self.use_ephemeral_databases is None:
            self.use_ephemeral_databases = settings.INSTANCE_EPHEMERAL_DATABASES
        super().save(**kwargs)

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
        gandi.set_dns_record(type='A', name=self.sub_domain, value=public_ip)
        self.logger.info('Updating DNS: Studio at %s...', self.studio_domain)
        gandi.set_dns_record(type='CNAME', name=self.studio_sub_domain, value=self.sub_domain)
        self.active_appserver = app_server
        self.save()

    @log_exception
    def spawn_appserver(self):
        """
        Provision a new AppServer. If it completes successfully, mark it as active.
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

        if app_server.provision():
            # If the AppServer provisioned successfully, make it the active one:
            # Note: if I call spawn_appserver() twice, and the second one provisions sooner, the first one may then
            # finish and replace the second as the active server. We are not really worried about that for now.
            self.set_appserver_active(app_server.pk)

post_save.connect(Instance.on_post_save, sender=OpenEdXInstance)
