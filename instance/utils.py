# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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
Instance app - Util functions
"""

# Imports #####################################################################

import itertools
import json
import logging
import selectors
import shutil
import socket
import time
from enum import Enum
from contextlib import contextmanager
from tempfile import mkdtemp
from typing import TYPE_CHECKING
from unittest.mock import Mock

import channels.layers
from django.conf import settings
import requests
from asgiref.sync import async_to_sync
from dictdiffer import diff

if TYPE_CHECKING:
    from registration.models import BetaTestApplication  # pylint: disable=cyclic-import, useless-suppression


# Logging #####################################################################

logger = logging.getLogger(__name__)


# Functions ###################################################################

def is_port_open(ip, port):
    """
    Check if the port is open on the provided ip
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    return sock.connect_ex((ip, port)) == 0


def to_json(obj):
    """
    Convert an object to a JSON string
    """

    def dumper(obj2):
        """
        Serializer that avoids throwing exceptions on objects it can't serialize
        """
        if isinstance(obj2, Mock):
            return repr(obj2)
        try:
            return obj2.toJSON()
        except Exception:  # pylint: disable=broad-except
            return repr(obj2)

    if not hasattr(obj, 'toJSON'):
        obj = obj.__dict__
    return json.dumps(obj, sort_keys=True, indent=4, default=dumper)


def get_requests_retry(total=10, connect=10, read=10, redirect=10, backoff_factor=0,
                       status_forcelist=settings.OPENSTACK_RETRYABLE_STATUS_CODES,
                       method_whitelist=settings.OPENSTACK_RETRYABLE_METHOD_WHITELIST):
    """
    Returns a urllib3 `Retry` object, with the default requests retry policy
    """
    return requests.packages.urllib3.util.retry.Retry(
        total=total,
        connect=connect,
        read=read,
        redirect=redirect,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        method_whitelist=method_whitelist,
    )


def _line_timeout_generator(line_timeout, global_timeout):
    """
    Helper function for poll_streams() to compute the timeout for a single line.
    """
    if global_timeout is not None:
        deadline = time.time() + global_timeout
        while True:
            global_timeout = deadline - time.time()
            if line_timeout is not None:
                yield min(line_timeout, global_timeout)
            else:
                yield global_timeout
    else:
        yield from itertools.repeat(line_timeout)


def poll_streams(*files, line_timeout=None, global_timeout=None):
    """
    Poll a set of file objects for new data and return it line by line.

    The file objects should be line-buffered or unbuffered.  Regular files won't
    work on some systems (notably Linux, where DefaultSelector uses epoll() by
    default; this function is pointless for regular files anyway, since they are
    always ready for reading and writing).

    Each line returned is a 2-items tuple, with the first item being the object
    implementing the file interface, and the second the text read.

    The optional parameters line_timeout and global_timeout specify how long in
    seconds to wait at most for a single line or for all lines.  If no timeout
    is specified, this function will block indefintely for each line.
    """
    selector = selectors.DefaultSelector()
    for fileobj in files:
        selector.register(fileobj, selectors.EVENT_READ)
    timeout = _line_timeout_generator(line_timeout, global_timeout)
    while selector.get_map():
        try:
            next_timeout = next(timeout)
        except StopIteration:
            logger.error('_line_timeout_generator returned (should never happen).'
                         'line_timeout: %s, global_timeout: %s',
                         line_timeout, global_timeout)
            next_timeout = 0
        available = selector.select(next_timeout)
        if not available:
            # TODO(smarnach): This can also mean that the process received a signal.
            raise TimeoutError('Could not read line before timeout: {timeout}'.format(timeout=timeout))
        for key, unused_mask in available:
            line = key.fileobj.readline()
            if line:
                yield (key.fileobj, line)
            else:
                selector.unregister(key.fileobj)


def sufficient_time_passed(earlier_date, later_date, expected_days_since):
    """
    Check if at least `expected_days_since` have passed between `earlier_date`
    and `later_date`.
    """
    days_passed = (later_date - earlier_date).days
    return days_passed >= expected_days_since


def publish_data(data):
    """
    Publish the data to the 'ws' group.
    """
    channel_layer = channels.layers.get_channel_layer()
    async_to_sync(channel_layer.group_send)('ws', {'type': 'notification', 'message': data})


def build_instance_config_diff(instance_config: 'BetaTestApplication', instance=None):
    """
    Builds an configuration diff for the provided instance configuration.
    """
    instance = instance
    if not instance:
        instance = object()
    original_config = {}
    new_config = {}
    for attr in ('instance_name', 'privacy_policy_url', 'public_contact_email'):
        original_config[attr] = getattr(instance, attr, None)
        new_config[attr] = getattr(instance_config, attr, None)

    original_config['theme_config'] = getattr(instance, 'theme_config', None) or {}
    new_config['theme_config'] = instance_config.draft_theme_config or {}
    original_config['static_content_overrides'] = getattr(instance, 'static_content_overrides', None) or {}
    new_config['static_content_overrides'] = instance_config.draft_static_content_overrides or {}

    return list(diff(original_config, new_config))


@contextmanager
def create_temp_dir():
    """
    A context manager that creates a temporary directory, returns it. Directory is deleted upon context manager exit.
    """
    temp_dir = None
    try:
        temp_dir = mkdtemp()
        yield temp_dir
    finally:
        # If tempdir is None it means that if wasn't created, so we don't need to delete it
        if temp_dir is not None:
            shutil.rmtree(temp_dir)


class DjangoChoiceEnum(Enum):
    """Enumeration that provides convenient methods for Django"""

    def __str__(self):
        return self.name

    @classmethod
    def choices(cls):
        """Render enum as tuple to use in Django choice field"""
        return tuple((prop.name, prop.value) for prop in cls)

    @classmethod
    def names(cls):
        """Return enum as list of string names """
        return list(prop.name for prop in cls)


def create_new_deployment(
        instance,
        creator=None,
        deployment_type=None,
        cancel_pending=False,
        add_delay=False,
        **kwargs,
):
    """
    Create a new deployment for an existing instance, and start it asynchronously
    """
    # pylint: disable=cyclic-import, useless-suppression
    from django.contrib.contenttypes.models import ContentType
    from grove.models.deployment import GroveDeployment
    from grove.models.instance import GroveInstance
    from grove.switchboard import SWITCH_GROVE_DEPLOYMENTS, is_feature_enabled
    from instance.models.deployment import DeploymentType
    from instance.models.openedx_deployment import DeploymentState, OpenEdXDeployment
    from instance.tasks import start_deployment
    from registration.models import BetaTestApplication

    changes = None
    if instance.betatestapplication.count() > 0:
        instance_type = ContentType.objects.get_for_model(instance)
        beta_test_application = BetaTestApplication.objects.filter(instance_type=instance_type, instance_id=instance.id)
        changes = build_instance_config_diff(beta_test_application[0], instance)

    deployment_type = deployment_type or DeploymentType.unknown
    creator_profile = creator and creator.profile

    # Check if the instance is managed by Grove
    if isinstance(instance, GroveInstance):
        project_id = instance.repository.project_id
        instance_id = instance.repository.unleash_instance_id
        # If the deployments are not enabled do not create a new deployment request. If the
        # instance has a repository configured that means it was deployed at least once by
        # Grove, hence OpenEdXInstance does not exist and creating an OpenEdXDeployment will
        # result in a broken app server. If the feature must be rolled back, all the instances
        # that were created by Grove should be revisited and new OpenEdXInstances should be
        # created for them. The reason this deployment behavior is controlled by a feature switch
        # is that we may need to roll back ASAP during the manual QA on production. Later, this
        # setting should be cleaned up as part of a cleanup task when Grove is deployed 100%.
        gitlab_client = instance.repository.gitlab_client
        if not is_feature_enabled(gitlab_client.base_url, project_id, instance_id, SWITCH_GROVE_DEPLOYMENTS):
            return

        GroveDeployment.objects.create(
            instance_id=instance.ref.id,
            creator=creator_profile,
            type=deployment_type,
            overrides=changes,
        )
        # In case of grove deployments, no scheduling needed as that's handled
        # by GitLab, therefore we need to return here.
        return

    if cancel_pending:
        deployment = instance.get_latest_deployment()
        if deployment.status() in (DeploymentState.changes_pending, DeploymentState.provisioning):
            deployment.cancel_deployment()
    if add_delay:
        # We delay the deployment instead of starting right now to give user some time to update the instance
        # without us having to setup and teardown the appserver.
        delay = settings.SELF_SERVICE_DEPLOYMENT_START_DELAY
    else:
        delay = 0
    deployment = OpenEdXDeployment.objects.create(
        instance_id=instance.ref.id,
        creator=creator_profile,
        type=deployment_type,
        changes=changes,
    )
    instance.logger.info('Deployment {} created. It will start after a delay of {}s.'.format(deployment.id, delay))
    start_deployment.schedule(
        args=(instance.ref.id, deployment.id),
        kwargs=kwargs,
        delay=delay
    )
