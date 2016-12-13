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
Instance app model mixins - load balancing
"""

# Imports #####################################################################

from django.conf import settings
from django.db import models

from instance import gandi
from instance.models.load_balancer import LoadBalancingServer


# Classes #####################################################################

class LoadBalancedInstance(models.Model):
    """
    Mixin for load-balanced instances.
    """
    load_balancing_server = models.ForeignKey(LoadBalancingServer, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        abstract = True

    def get_load_balanced_domains(self):  # pylint: disable=no-self-use
        """
        Return an iterable of domains that should be handled by the load balancer.
        """
        return []

    def get_managed_domains(self):  # pylint: disable=no-self-use
        """
        Return an iterable of domains that we  manage DNS entries for.
        """
        return []

    def set_dns_records(self):
        """
        Create CNAME records for the domain names of this instance pointing to the load balancer.
        """
        load_balancer_domain = self.load_balancing_server.domain.rstrip(".") + "."
        for domain in self.get_managed_domains():
            gandi.api.set_dns_record(domain, type="CNAME", value=load_balancer_domain)

    def remove_dns_records(self):
        """
        Delete the DNS records for this instance.
        """
        for domain in self.get_managed_domains():
            gandi.api.remove_dns_record(domain)

    def reconfigure_load_balancer(self, load_balancing_server=None):
        """
        Reconfigure the associated load balancer.
        """
        if load_balancing_server is None:
            load_balancing_server = self.load_balancing_server
            if load_balancing_server is None:
                return
        self.logger.info("Triggering reconfiguration of the load balancing server...")
        load_balancing_server.reconfigure(self.ref.pk)

    def get_preliminary_page_config(self, primary_key):
        """
        Return a load balancer configuration for the preliminary page.
        """
        if not settings.PRELIMINARY_PAGE_SERVER_IP:
            self.logger.info(
                "Not configuring the preliminary page since PRELIMINARY_PAGE_SERVER_IP is not set."
            )
            return [], []
        self.logger.info("Configuring load balancer to point to the preliminary page.")
        backend_name = "be-preliminary-page-{}".format(primary_key)
        config = "    server preliminary-page {}:80".format(settings.PRELIMINARY_PAGE_SERVER_IP)
        backend_map = [(domain, backend_name) for domain in self.get_load_balanced_domains()]
        return backend_map, [(backend_name, config)]
