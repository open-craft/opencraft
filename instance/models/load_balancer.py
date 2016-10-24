# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <xavier@opencraft.com>
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
Definition of the Load balancing server model.
"""
import logging
import os
import random
import subprocess

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction
from django.template import loader

from instance.logging import ModelLoggerAdapter
from .instance import Instance
from .utils import ValidateModelMixin


logger = logging.getLogger(__name__)


def run_ssh_script(server, username, script, sudo=True):
    """Run a script via SSH on the given server."""
    if sudo:
        command = "sudo sh"
    else:
        command = "sh"
    subprocess.run(
        ["ssh", "-T", "-o", "PasswordAuthentication=no", "-l", username, server, command],
        input=script.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=settings.ANSIBLE_LINE_TIMEOUT,
        check=True,
    )


class LoadBalancingServer(ValidateModelMixin, models.Model):
    """A model representing a configured load-balancing server."""

    domain = models.CharField(max_length=100, unique=True)
    # The username used to ssh into the server
    ssh_username = models.CharField(max_length=32)
    # Whether new backends can be assigned to this load-balancing server
    accepts_new_backends = models.BooleanField(default=True)
    # A random postfix appended to the haproxy configuration file names to make collisions
    # impossible.
    fragment_name_postfix = models.CharField(max_length=8, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ModelLoggerAdapter(logger, {'obj': self})

    def __str__(self):
        return self.domain

    def get_log_message_annotation(self):
        """Annotate log messages for the load-balancing server."""
        return "load_balancer={} ({!s:.15})".format(self.pk, self.domain)

    def get_instances(self):
        """Yield all instances configured to use this load balancer."""
        for field in self._meta.get_fields():
            if field.one_to_many and issubclass(field.related_model, Instance):
                yield from getattr(self, field.get_accessor_name()).iterator()

    def get_configuration(self):
        """Collect the backend maps and configuration fragments from all associated instances."""
        backend_map = []
        backend_conf = []
        for instance in self.get_instances():
            map_entries, conf = instance.get_load_balancer_configuration()
            backend_map.append(map_entries)
            backend_conf.append(conf)
        return "\n\n".join(backend_map), "\n\n".join(backend_conf)

    def get_fragment_name(self):
        """Return the base name to use for the haproxy configuration files.

        This should be unique for each instance of the instance manager, so that different
        instance managers can share a load balancing server.
        """
        if not self.fragment_name_postfix:
            bits = self._meta.get_field("fragment_name_postfix").max_length * 4
            self.fragment_name_postfix = format(random.getrandbits(bits), "x")
            self.save()
        return settings.LOAD_BALANCER_FRAGMENT_NAME_PREFIX + self.fragment_name_postfix

    def get_config_script(self):
        """Render the configuration script to be executed on the loader balancer."""
        backend_map, backend_conf = self.get_configuration()
        fragment_name = self.get_fragment_name()
        template = loader.get_template("instance/haproxy/conf.sh")
        return template.render(dict(
            settings=settings,
            conf_filename=os.path.join(settings.LOAD_BALANCER_CONF_DIR, fragment_name),
            backend_conf=backend_conf,
            backend_filename=os.path.join(settings.LOAD_BALANCER_BACKENDS_DIR, fragment_name),
            backend_map=backend_map,
        ))

    def reconfigure(self):
        """Regenerate the configuration fragments on the load-balancing server."""
        self.logger.info("Reconfiguring load-balancing server %s", self.domain)
        config_script = self.get_config_script()
        try:
            run_ssh_script(self.domain, self.ssh_username, config_script)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            self.logger.error(
                "Reconfiguring the load balancer failed.  Stderr of ssh process:\n%s",
                exc.stderr,
            )
            raise


def _create_default_load_balancing_server():
    """Create the default load balancing server configured in the Django settings, if any."""
    if settings.DEFAULT_LOAD_BALANCING_SERVER:
        ssh_username, unused, domain = settings.DEFAULT_LOAD_BALANCING_SERVER.partition("@")
        if not ssh_username or not domain:
            raise ImproperlyConfigured(
                "DEFAULT_LOAD_BALANCING_SERVER must have the form ssh_username@domain.name."
            )
        logger.info("Creating LoadBalancingServer %s", domain)
        server, created = LoadBalancingServer.objects.get_or_create(
            domain=domain,
            defaults=dict(ssh_username=ssh_username),
        )
        if not created and server.ssh_username != ssh_username:
            logger.warning(
                "The SSH username of LoadBalancingServer %s in database does not match the "
                "username in Django settings@ %s vs %s",
                domain, server.ssh_username, ssh_username
            )


def select_load_balancing_server():
    """Select a load-balancing server for a new instance.

    The current implementation selects one of the load balancers that accept new backends at
    random.  If no load-balancing server accepts new backends, LoadBalancingServer.DoesNotExist
    is raised.
    """
    _create_default_load_balancing_server()

    # The set of servers might change between retrieving the server count and retrieving the random
    # server, so we make this atomic.
    with transaction.atomic():
        servers = LoadBalancingServer.objects.filter(accepts_new_backends=True)
        count = servers.count()
        if not count:
            raise LoadBalancingServer.DoesNotExist(
                "No configured LoadBalancingServer accepts new backends."
            )
        return servers[random.randrange(count)]
