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
Convenience wrappers for calls to the Nomad REST API.
"""

# Imports #####################################################################

import functools

from django.conf import settings
import requests


# Functions ###################################################################

def request(method, *endpoint_parts, server=settings.NOMAD_SERVER, version="v1", **kwargs):
    """Send a REST API request to the Nomad API and return the Response object."""
    url = "https://" + "/".join([server, version, *endpoint_parts])
    kwargs.setdefault("verify", settings.NOMAD_CACERT)
    kwargs.setdefault("cert", (settings.NOMAD_CLIENT_CERT, settings.NOMAD_CLIENT_KEY))
    kwargs.setdefault("timeout", 15)
    return requests.request(method, url, **kwargs)

# Convenience wrappers for specific HTTP methods
get = functools.partial(request, "get")
post = functools.partial(request, "post")
put = functools.partial(request, "put")
delete = functools.partial(request, "delete")


# Classes #####################################################################

class NomadJob:
    """Class to represent a Nomad job.

    This representation is meant to be ephemeral, and it is not persisted to the database.
    """

    def __init__(self, jobspec):
        """Initialize a NomadJob instance.

        The jobspec parameter is expected to be a dictionary that can be serialized to a valid JSON
        jobspec.
        """
        self.jobspec = jobspec
        self.job_id = jobspec["ID"]

    def run(self):
        """Create the job on the Nomad cluster."""
        return post("jobs", json={"Job": self.jobspec})

    def stop(self):
        """Delete the job from the Nomad cluster."""
        return delete("job", self.job_id)

    def all_running(self):
        """Return a Boolean value indicating whether all desired task groups are running."""
        # This function is somewhat improvised.  The status of a Nomad job is rather complex, since
        # all task groups and their allocations have their own status.  This implementation aims
        # to be a reasonable simple way of determining whether the job started successfully.  I
        # would prefer to rely on Consul health checks instead, but currently I don't know a way of
        # making them work properly together with Consul Connect.
        response = get("job", self.job_id, "summary")
        if response.status_code == 404:
            return False
        response.raise_for_status()
        summary = response.json()["Summary"]
        return all(
            summary[task_group["Name"]]["Running"] >= task_group["Count"]
            for task_group in self.jobspec["TaskGroups"]
        )
