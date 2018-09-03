# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
Mixin for instances that depend on Nomad jobs.
"""

# Imports #####################################################################

import time

from django.db import models


# Classes #####################################################################

class NomadTimeoutError(Exception):
    """Exception indicating that a Nomad operation did not complete within the expected time."""


class NomadJobMixin(models.Model):
    """A mixin for an Instance subclass to launch Nomad jobs."""

    class Meta:
        abstract = True

    def get_nomad_jobs(self): # pylint: disable=no-self-use
        """Return an iterable of instance.nomad_client.NomadJob instances describing the job to run.

        This method should be overwritten in subclasses.
        """
        return []

    def provision_nomad_jobs(self, timeout=120):
        """Launch all Nomad jobs and wait for the to come up.

        If the jobs don't come up within timeout seconds, a NomadTimeoutError will be raised.
        """
        jobs = self.get_nomad_jobs()
        for job in jobs:
            response = job.run()
            # We want the provisioning of an app server to fail if we can't create a Nomad job, so
            # we raise an exception for HTTP errors.
            response.raise_for_status()

        time_limit = time.time() + timeout
        while True:
            if all(job.all_running() for job in jobs):
                return
            if time.time() > time_limit:
                raise NomadTimeoutError("Not all Nomad jobs could be started within the timeout.")
            time.sleep(1)

    def deprovision_nomad_jobs(self):
        """Stop all Nomad jobs again."""
        for job in self.get_nomad_jobs():
            try:
                response = job.stop()
                response.raise_for_status()
            except Exception:  # pylint: disable=broad-except
                # We suppress the exception, since we still want instances to be successfully
                # archived even if we can't delete all Nomad jobs.  This may leak jobs, but it's
                # still the lesser evil, and we simply don't have a design that allows tracking
                # all resources in all circumstances.  That's why we plan to move to Terraform.
                self.logger.exception(
                    'An error occurred when trying to remove the Nomad job "%s"',
                    job.id,
                )
