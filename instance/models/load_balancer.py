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
import pathlib
import random
import textwrap

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction
from django_extensions.db.models import TimeStampedModel

from instance import ansible
from instance.logging import ModelLoggerAdapter
from instance.models.utils import ValidateModelMixin


logger = logging.getLogger(__name__)


class LoadBalancingServerManager(models.Manager):
    """
    Custom manager for the LoadBalancingServer model.
    """
    def _create_default(self):
        """
        Create the default load balancing server configured in the Django settings, if any.
        """
        if settings.DEFAULT_LOAD_BALANCING_SERVER:
            ssh_username, unused, domain = settings.DEFAULT_LOAD_BALANCING_SERVER.partition("@")
            if not ssh_username or not domain:
                raise ImproperlyConfigured(
                    "DEFAULT_LOAD_BALANCING_SERVER must have the form ssh_username@domain.name."
                )
            logger.info("Creating LoadBalancingServer %s", domain)
            server, created = self.get_or_create(  # pylint: disable=no-member
                domain=domain,
                defaults=dict(ssh_username=ssh_username),
            )
            if not created and server.ssh_username != ssh_username:
                logger.warning(
                    "The SSH username of LoadBalancingServer %s in database does not match the "
                    "username in Django settings@ %s vs %s",
                    domain, server.ssh_username, ssh_username
                )

    def select_random(self):
        """
        Select a load-balancing server for a new instance.

        The current implementation selects one of the load balancers that accept new backends at
        random.  If no load-balancing server accepts new backends, LoadBalancingServer.DoesNotExist
        is raised.
        """
        self._create_default()

        # The set of servers might change between retrieving the server count and retrieving the random
        # server, so we make this atomic.
        with transaction.atomic():
            servers = self.filter(accepts_new_backends=True)  # pylint: disable=no-member
            count = servers.count()
            if not count:
                raise self.model.DoesNotExist(  # pylint: disable=no-member
                    "No configured LoadBalancingServer accepts new backends."
                )
            return servers[random.randrange(count)]


class ReconfigurationFailed(Exception):
    """Exception indicating that reconfiguring the load balancer failed."""


class LoadBalancingServer(ValidateModelMixin, TimeStampedModel):
    """
    A model representing a configured load-balancing server.
    """
    objects = LoadBalancingServerManager()

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

    def set_field_defaults(self):
        if not self.fragment_name_postfix:
            # Set a unique fragment_name_postfix to avoid clashes between multiple instance
            # managers sharing the same load balancer.
            bits = self._meta.get_field("fragment_name_postfix").max_length * 4
            self.fragment_name_postfix = format(random.getrandbits(bits), "x")
        super().set_field_defaults()

    def __str__(self):
        return self.domain

    def get_log_message_annotation(self):
        """
        Annotate log messages for the load-balancing server.
        """
        return "load_balancer={} ({!s:.15})".format(self.pk, self.domain)

    def get_instances(self):
        """
        Yield all instances configured to use this load balancer.
        """
        # Local import due to avoid problems with circular dependencies.
        from instance.models.mixins.load_balanced import LoadBalancedInstance

        for field in self._meta.get_fields():
            if field.one_to_many and issubclass(field.related_model, LoadBalancedInstance):
                yield from getattr(self, field.get_accessor_name()).iterator()

    def get_configuration(self, triggering_instance_id=None):
        """
        Collect the backend maps and configuration fragments from all associated instances.

        This function also appends fragment_name_postfix to all backend names to avoid name clashes
        between multiple instance managers using the same load balancer (e.g. for the integration
        tests).

        The triggering_instance_id indicates the id of the instance reference that initiated the
        reconfiguration of the load balancer.
        """
        backend_map = []
        backend_conf = []
        for instance in self.get_instances():
            triggered_by_instance = instance.ref.pk == triggering_instance_id
            map_entries, conf_entries = instance.get_load_balancer_configuration(
                triggered_by_instance
            )
            backend_map.extend(
                " ".join([domain.lower(), backend + self.fragment_name_postfix])
                for domain, backend in map_entries
            )
            backend_conf.extend(
                "backend {}\n{}\n".format(backend + self.fragment_name_postfix, conf)
                for backend, conf in conf_entries
            )
        return "\n".join(backend_map), "\n".join(backend_conf)

    def get_ansible_vars(self, triggering_instance_id=None):
        """
        Render the configuration script to be executed on the load balancer.

        The triggering_instance_id indicates the id of the instance reference that initiated the
        reconfiguration of the load balancer.
        """
        backend_map, backend_conf = self.get_configuration(triggering_instance_id)
        fragment_name = settings.LOAD_BALANCER_FRAGMENT_NAME_PREFIX + self.fragment_name_postfix
        return (
            "FRAGMENT_NAME: {fragment_name}\n"
            "BACKEND_CONFIG_FRAGMENT: |\n"
            "{backend_conf}\n"
            "BACKEND_MAP_FRAGMENT: |\n"
            "{backend_map}\n"
        ).format(
            fragment_name=fragment_name,
            backend_conf=textwrap.indent(backend_conf, "  "),
            backend_map=textwrap.indent(backend_map, "  "),
        )

    def run_playbook(self, ansible_vars):
        """
        Run the playbook to perform the server reconfiguration.

        This is factored out into a separate method so it can be mocked out in the tests.
        """
        playbook_path = pathlib.Path(settings.SITE_ROOT) / "playbooks/load_balancer_conf/load_balancer_conf.yml"
        with cache.lock(self.domain):
            returncode = ansible.capture_playbook_output(
                requirements_path=str(playbook_path.parent / "requirements.txt"),
                inventory_str=self.domain,
                vars_str=ansible_vars,
                playbook_path=str(playbook_path),
                username=self.ssh_username,
                logger_=self.logger,
            )
        if returncode != 0:
            self.logger.error("Playbook to reconfigure load-balancing server %s failed.", self)
            raise ReconfigurationFailed

    def reconfigure(self, triggering_instance_id=None):
        """
        Regenerate the configuration fragments on the load-balancing server.

        The triggering_instance_id indicates the id of the instance reference that initiated the
        reconfiguration of the load balancer.
        """
        self.logger.info("Reconfiguring load-balancing server %s", self.domain)
        self.run_playbook(self.get_ansible_vars(triggering_instance_id))

    def deconfigure(self):
        """
        Remove the configuration fragment from the load-balancing server.
        """
        fragment_name = settings.LOAD_BALANCER_FRAGMENT_NAME_PREFIX + self.fragment_name_postfix
        self.run_playbook(
            "FRAGMENT_NAME: {fragment_name}\nREMOVE_FRAGMENT: True".format(fragment_name=fragment_name)
        )

    def delete(self, *args, **kwargs):
        """
        Delete the LoadBalancingServer from the database.
        """
        self.deconfigure()
        super().delete(*args, **kwargs)  # pylint: disable=no-member
