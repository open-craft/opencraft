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
Definition of the Load balancing server model.
"""
import contextlib
import functools
import logging
import pathlib
import random
import textwrap

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django_extensions.db.models import TimeStampedModel

from instance import ansible
from instance.logging import ModelLoggerAdapter
from instance.models.shared_server import SharedServerManager
from instance.models.utils import ValidateModelMixin


logger = logging.getLogger(__name__)


class LoadBalancingServerManager(SharedServerManager):
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
            server, created = self.get_or_create(
                domain=domain,
                defaults=dict(
                    ssh_username=ssh_username,
                    accepts_new_backends=True,
                ),
            )
            if not created and server.ssh_username != ssh_username:
                logger.warning(
                    "The SSH username of LoadBalancingServer %s in database does not match the "
                    "username in Django settings@ %s vs %s",
                    domain, server.ssh_username, ssh_username
                )

    def filter_accepts_new_clients(self):
        """
        Returns a query selector of servers accepting new clients.
        """
        return self.filter(accepts_new_backends=True)


class ReconfigurationException(Exception):
    """Base class exception relating to reconfiguration errors."""


class ReconfigurationFailed(ReconfigurationException):
    """Exception indicating that reconfiguring the load balancer failed."""


class OtherReconfigurationInProgress(ReconfigurationException):
    """Exception indicating that another reconfiguration is already in progress."""


def generate_fragment_name(length):
    """
    Helper function to set the default value of the field `fragment_name_postfix`.
    """
    return format(random.getrandbits(length * 4), "x")


class LoadBalancingServer(ValidateModelMixin, TimeStampedModel):
    """
    A model representing a configured load-balancing server.
    """
    objects = LoadBalancingServerManager()

    domain = models.CharField(max_length=100, unique=True)

    ssh_username = models.CharField(
        max_length=32,
        help_text='The username used to SSH into the server.'
    )

    accepts_new_backends = models.BooleanField(
        default=False,
        help_text='Whether new backends can be assigned to this load-balancing server.'
    )

    fragment_name_postfix = models.CharField(
        max_length=8,
        blank=True,
        default=functools.partial(generate_fragment_name, length=8),
        help_text=(
            'A random postfix appended to the haproxy configuration file names to avoid clashes between '
            'multiple instance managers (or multiple concurrently running integration tests) sharing the '
            'same load balancer.'
        )
    )

    configuration_version = models.PositiveIntegerField(
        default=1,
        help_text=(
            'The current version of configuration for this load balancer. '
            'The version value is the total number of requests ever made to reconfigure the load balancer.'
        )
    )

    deployed_configuration_version = models.PositiveIntegerField(
        default=1,
        help_text=(
            'The currently active configuration version of the load balancer. '
            'If it is less than the configuration version, the load balancer is dirty. '
            'If it is equal to it, then no new reconfiguration is currently required.'
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ModelLoggerAdapter(logger, {'obj': self})

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
        # pylint: disable=cyclic-import
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
        if settings.DISABLE_LOAD_BALANCER_CONFIGURATION:
            self.logger.info(
                'Direct load balancer reconfiguration disabled. Skipping %s configuration...',
                self
            )
            return "", ""

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
        if settings.DISABLE_LOAD_BALANCER_CONFIGURATION:
            self.logger.info(
                'Direct load balancer reconfiguration disabled. Skipping %s configuration...',
                self
            )
            return

        playbook_path = pathlib.Path(settings.SITE_ROOT) / "playbooks/load_balancer_conf/load_balancer_conf.yml"
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

    def reconfigure(self, triggering_instance_id=None, mark_dirty=True):
        """
        Regenerate the configuration fragments on the load-balancing server.

        The triggering_instance_id indicates the id of the instance reference that initiated the
        reconfiguration of the load balancer.

        The mark_dirty flag indicates whether the LB configuration should be marked as dirty.  If
        this method is called because the configuration changed, the flag should be set to True (the
        default).  If this method is called because the LB was marked dirty earlier, the flag
        should be set to False.
        """
        if mark_dirty:
            # We need to use an F expression here.  The problem is not other processes trying to
            # increase this counter concurrently – that wouldn't matter, since we don't care whether
            # we increase this counter by one or by two, since both marks the LB as dirty.  However, if
            # another process is making a completely unrelated change to the LB object we might lose
            # the increment altogether.
            LoadBalancingServer.objects.filter(pk=self.pk).update(
                configuration_version=models.F("configuration_version") + 1
            )

        try:
            with self._configuration_lock(blocking=False):
                # Memorize the configuration version, in case new threads change it.
                self.refresh_from_db()
                candidate_configuration_version = self.configuration_version
                self.logger.info("Reconfiguring load-balancing server %s", self.domain)
                self.run_playbook(self.get_ansible_vars(triggering_instance_id))
                LoadBalancingServer.objects.filter(pk=self.pk).update(
                    deployed_configuration_version=candidate_configuration_version
                )
                self.refresh_from_db()
        except OtherReconfigurationInProgress:
            pass

    def deconfigure(self):
        """
        Remove the configuration fragment from the load-balancing server.
        """
        self.logger.info("Deconfiguring load-balancing server %s", self.domain)
        fragment_name = settings.LOAD_BALANCER_FRAGMENT_NAME_PREFIX + self.fragment_name_postfix
        with self._configuration_lock():
            self.run_playbook(
                "FRAGMENT_NAME: {fragment_name}\nREMOVE_FRAGMENT: True".format(fragment_name=fragment_name)
            )

    def delete(self, **kwargs):
        """
        Delete the LoadBalancingServer from the database.
        """
        self.deconfigure()
        super().delete(**kwargs)

    @contextlib.contextmanager
    def _configuration_lock(self, *, blocking=True):
        """
        A Redis lock to protect reconfigurations of this load balancer instance.
        """
        lock = cache.lock(
            "load_balancer_reconfigure:{}".format(self.domain),
            timeout=settings.REDIS_LOCK_TIMEOUT,
        )
        if not lock.acquire(blocking):
            raise OtherReconfigurationInProgress
        try:
            yield lock
        finally:
            lock.release()
