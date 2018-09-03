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
Redis and Memcache Nomad job definitions for Open edX instances.
"""

# Imports #####################################################################

from django.conf import settings

from instance.models.mixins.nomad_jobs import NomadJobMixin
from instance.nomad_client import NomadJob


# Functions ###################################################################

def _jobspec_task(name, command, args, memory, cpu=20, disk=0, net_mbits=1):
    """Helper function to create a task in a Nomad jobspec."""
    return {
        "Name": name,
        "Driver": "raw_exec",
        "Config": {
            "command": command,
            "args": args,
        },
        "Resources": {
            "CPU": cpu,
            "MemoryMB": memory,
            "DiskMB": disk,
            "Networks": [
                {
                    "MBits": net_mbits,
                    "DynamicPorts": [
                        {"Label": "main"},
                    ],
                },
            ],
        },
    }


def _jobspec(
        job_id, count, server_command, server_args,
        server_memory=32, service_include_alloc_id=False):
    """Helper function to create a Nomad jobspec for a server job with consul connect sidecar."""
    if service_include_alloc_id:
        service_name = job_id + "-${NOMAD_ALLOC_INDEX}"
    else:
        service_name = job_id
    return {
        "ID": job_id,
        "Name": job_id,
        "Type": "service",
        "Datacenters": ["dc1"],
        "Constraints": [
            {"Operand": "distinct_hosts"},
        ],
        "TaskGroups": [
            {
                "Name": "server",
                "Count": count,
                "Tasks": [
                    _jobspec_task(
                        name="server",
                        command=server_command,
                        args=server_args,
                        memory=server_memory,
                    ),
                    _jobspec_task(
                        name="connect-proxy",
                        command="/usr/local/bin/consul",
                        args=[
                            "connect", "proxy",
                            "-service", service_name,
                            "-service-addr", "127.0.0.1:${NOMAD_PORT_server_main}",
                            "-listen", ":${NOMAD_PORT_main}",
                            "-register"
                        ],
                        memory=20,
                    ),
                ]
            }
        ],
        "Update": {
            "MaxParallel": 1
        },
        "Migrate": {
            "MaxParallel": 1
        }
    }


# Classes #####################################################################

class OpenEdXNomadJobMixin(NomadJobMixin):
    """Redis and Memcache Nomad job definitions for Open edX instances."""

    class Meta:
        abstract = True

    def get_nomad_jobs(self):
        """Return an iterable of instance.nomad_client.NomadJob instances describing the job to run.

        This method should be overwritten in subclasses.
        """
        return [
            NomadJob(_jobspec(
                job_id="redis-{}".format(self.id),
                count=1,
                server_command="/usr/bin/redis-server",
                server_args=[
                    # Listen only on localhost
                    "--bind", "127.0.0.1",
                    # TCP port
                    "--port", "${NOMAD_PORT_main}",
                ],
            )),
            NomadJob(_jobspec(
                job_id="memcached-{}".format(self.id),
                count=settings.INSTANCE_MEMCACHED_JOB_COUNT,
                server_command="/usr/bin/memcached",
                server_args=[
                    # Log to stdout
                    "-v",
                    # Listen only on localhost
                    "-l", "127.0.0.1",
                    # TCP port
                    "-p", "${NOMAD_PORT_main}",
                    # Memory limit.  The daemon won't use more than the limit, but may use significantly less.
                    "-m", "64", # MB
                    # Become user "memcache" after starting
                    "-u", "memcache",
                ],
                service_include_alloc_id=True,
            )),
        ]
