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
Instance app model mixins - RabbitMQ
"""

# Imports #####################################################################

import pathlib

from django.conf import settings
from django.db import models

from instance.ansible import capture_playbook_output
from instance.models.rabbitmq import RabbitMQUser


# Classes #####################################################################

class ReconfigurationFailed(Exception):
    """Exception indicating that reconfiguring RabbitMQ failed."""


class RabbitMQInstanceMixin(models.Model):
    """
    An instance that uses a RabbitMQ vhost with a set of users.
    """
    rabbitmq_vhost = models.CharField(max_length=16, blank=True)
    rabbitmq_provider_user = models.ForeignKey(
        RabbitMQUser,
        related_name='provider_instance',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    rabbitmq_consumer_user = models.ForeignKey(
        RabbitMQUser,
        related_name='consumer_instance',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    rabbitmq_provisioned = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def _get_rabbitmq_vars(self, remove):
        """
        Generate the vars string for the RabbitMQ playbook.
        """
        users = ''.join([
            '- username: {username}\n  password: {password}\n'.format(username=user.username, password=user.password)
            for user in [self.rabbitmq_provider_user, self.rabbitmq_consumer_user]
        ])
        ansible_vars = 'STATE: {state}\nRABBITMQ_VHOST: {vhost}\nRABBITMQ_USERS:\n{users}'.format(
            state='absent' if remove else 'present',
            vhost=self.rabbitmq_vhost,
            users=users
        )

        return ansible_vars

    def _run_rabbitmq_playbook(self, remove):
        """
        Run the RabbitMQ playbook to reconfigure add/remove a vhost and users.
        """
        playbook_path = pathlib.Path(settings.SITE_ROOT) / "playbooks/rabbitmq_conf/rabbitmq_conf.yml"
        returncode = capture_playbook_output(
            requirements_path=str(playbook_path.parent / "requirements.txt"),
            inventory_str=settings.INSTANCE_RABBITMQ_HOST,
            vars_str=self._get_rabbitmq_vars(remove),
            playbook_path=str(playbook_path),
            username=settings.INSTANCE_RABBITMQ_SSH_USERNAME,
            logger_=self.logger,
        )
        if returncode != 0:
            self.logger.error("Playbook to reconfigure RabbitMQ server %s failed.", self)
            raise ReconfigurationFailed

        return returncode

    def provision_rabbitmq(self):
        """
        Create RabbitMQ vhost and users
        """
        if not self.rabbitmq_provisioned:
            self._run_rabbitmq_playbook(False)
        self.rabbitmq_provisioned = True
        self.save()

    def deprovision_rabbitmq(self):
        """
        Delete RabbitMQ vhost and users
        """
        if self.rabbitmq_provisioned:
            self._run_rabbitmq_playbook(True)
        self.rabbitmq_provisioned = False
        self.save()
