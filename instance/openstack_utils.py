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
OpenStack - Helper functions
"""

# Imports #####################################################################
import logging
from collections import namedtuple, defaultdict

from django.conf import settings
from novaclient.client import Client as NovaClient
from openstack.connection import Connection
from openstack.profile import Profile
import requests
from swiftclient.service import SwiftService

from instance.utils import get_requests_retry

# Logging #####################################################################

logger = logging.getLogger(__name__)

# Data objects ################################################################

FailedContainer = namedtuple('FailedContainer', ['name', 'number_of_failures'])
StatContainer = namedtuple('StatContainer', ['read_acl', 'write_acl', 'bytes'])
# A simplified version of openstack.network.v2.security_group_rule.SecurityGroupRule
# This version removes fields like 'id', 'security_group_id', 'updated_at' so
# that these rules can be compared across servers/time/space.
SecurityGroupRuleDefinition = namedtuple('SecurityGroupRuleDefinition', [
    # See http://developer.openstack.org/sdks/python/openstacksdk/users/resources/network/v2/security_group_rule.html
    # for details on the supported values of these fields
    'direction',  # 'ingress' or 'egress'
    'ether_type',  # 'IPv4' or 'IPv6'
    'protocol',  # None, 'tcp', 'udp', 'icmp'
    'port_range_min',
    'port_range_max',
    # One of the following must be None and the other must be a string:
    'remote_ip_prefix',  # e.g. '0.0.0.0/0'
    'remote_group_id',
])

# Functions ###################################################################


# TODO: refactor to take in all connection settings as parameters
def get_openstack_connection(region_name):
    """
    Get the OpenStack Connection object.

    This is the new, all-powerful Python API for OpenStack. It should be used
    instead of the service-specific APIs such as the Nova API below.

    The returned Connection object has an attribute for each available service,
    e.g. "compute", "network", etc.
    """
    profile = Profile()
    profile.set_region(Profile.ALL, region_name)
    connection = Connection(
        profile=profile,
        user_agent='opencraft-im',
        auth_url=settings.OPENSTACK_AUTH_URL,
        project_name=settings.OPENSTACK_TENANT,
        username=settings.OPENSTACK_USER,
        password=settings.OPENSTACK_PASSWORD,
    )
    # API queries via the nova client occasionally get connection errors from the OpenStack provider.
    # To gracefully recover when the unavailability is short-lived, ensure safe requests (as per
    # urllib3's definition) are retried before giving up.
    adapter = requests.adapters.HTTPAdapter(max_retries=get_requests_retry())
    connection.session.session.mount('http://', adapter)
    connection.session.session.mount('https://', adapter)
    return connection


def sync_security_group_rules(security_group, rule_definitions, network):
    """
    Given an OpenStack 'SecurityGroup' instance and a list of rules (in the form
    of SecurityGroupRuleDefinition tuples), ensure that the security group's
    rules match the provided rules. Add/delete rules from the remote security
    group until it matches 'rules'.
    """
    assert all(isinstance(rule, SecurityGroupRuleDefinition) for rule in rule_definitions)
    rule_definitions_set = set(rule_definitions)

    existing_rules = network.security_group_rules(security_group_id=security_group.id)
    for existing_rule in existing_rules:
        # Simplify this rule by converting from a 'SecurityGroupRule' to a 'SecurityGroupRuleDefinition':
        rule_definition = SecurityGroupRuleDefinition(
            **{key: getattr(existing_rule, key) for key in SecurityGroupRuleDefinition._fields}
        )

        if rule_definition in rule_definitions_set:
            # This rule exists, as expected.
            rule_definitions_set.remove(rule_definition)
        else:
            # This rule that was found on the remote server is not in the list of desired rules.
            # Delete it.
            logger.info("Updating network security group %s to remove %s", security_group.name, rule_definition)
            network.delete_security_group_rule(existing_rule)

    # Any rule left in rule_definitions_set is one that needs to be created:
    for rule_definition in rule_definitions_set:
        logger.info("Updating network security group %s to add %s", security_group.name, rule_definition)
        network.create_security_group_rule(security_group_id=security_group.id, **rule_definition._asdict())


# TODO: refactor to take in all connection settings as parameters
def get_nova_client(region_name, api_version=2):
    """
    Instantiate a python novaclient.Client() object with proper credentials
    """
    nova = NovaClient(
        api_version,
        settings.OPENSTACK_USER,
        settings.OPENSTACK_PASSWORD,
        settings.OPENSTACK_TENANT,
        settings.OPENSTACK_AUTH_URL,
        region_name=region_name,
    )

    # API queries via the nova client occasionally get connection errors from the OpenStack provider.
    # To gracefully recover when the unavailability is short-lived, ensure safe requests (as per
    # urllib3's definition) are retried before giving up.
    adapter = requests.adapters.HTTPAdapter(max_retries=get_requests_retry())
    nova.client.open_session()
    nova.client._session.mount('http://', adapter)
    nova.client._session.mount('https://', adapter)

    return nova


def create_server(nova, server_name, flavor_selector, image_selector, key_name=None, security_groups=None):
    """
    Create a VM via nova
    """
    flavor = nova.flavors.find(**flavor_selector)
    image = nova.images.find(**image_selector)

    logger.info('Creating OpenStack server: name=%s image=%s flavor=%s', server_name, image, flavor)
    return nova.servers.create(server_name, image, flavor, key_name=key_name, security_groups=security_groups)


def get_server_public_address(server, ip_version=4):
    """
    Retrieve the public IP of `server` with the given `ip_version` (default 4).
    """
    addresses = server.addresses
    if not addresses:
        return None

    # Return the first address with the given IP version
    for address_list in addresses.values():
        # TODO: Ensure it is public, e.g. OVH addresses have key='Ext-Net'
        for address in address_list:
            if int(address.get('version', 0)) == ip_version:
                return address

    return None


# TODO: refactor to take in auth_version as parameter.
def swift_service(
        user=settings.SWIFT_OPENSTACK_USER,
        password=settings.SWIFT_OPENSTACK_PASSWORD,
        tenant=settings.SWIFT_OPENSTACK_TENANT,
        auth_url=settings.SWIFT_OPENSTACK_AUTH_URL,
        region=settings.SWIFT_OPENSTACK_REGION):
    """
    Creates a swift service.
    """

    return SwiftService(options=dict(
        auth_version='2',
        os_username=user,
        os_password=password,
        os_tenant_name=tenant,
        os_auth_url=auth_url,
        os_region_name=region,
    ))


def stat_container(container_name, **kwargs):
    """
    Stat a container.
    :param str container_name:  name of the container
    :param dict kwargs: passed to swift_service
    :rtype: StatContainer
    """
    with swift_service(**kwargs) as service:
        stat_result = service.stat(container_name)
        stat_response = dict(stat_result['items'])
        return StatContainer(
            read_acl=stat_response['Read ACL'],
            write_acl=stat_response['Write ACL'],
            bytes=stat_response['Bytes']
        )


def download_swift_account(download_target, **kwargs):
    """
    :param str download_target: Directory to download to
    :param dict kwargs: Auth parameters passed to `swift_service`.
    :return: List of FailedContainer objects. If all list is emtpy all
             containers backed up successfully.
    """

    errors = defaultdict(lambda: 0)

    with swift_service(**kwargs) as service:
        downloader = service.download(options={
            'yes_all': True,  # Download whole account
            'skip_identical': True,  # Check file checksum locally and if the same don't download,
            'out_directory': download_target  # Set folder where to download
        })
        for file_download_result in downloader:
            if not file_download_result['success']:

                # For some reason Swift treats file not modified as an error
                if file_download_result['response_dict']['status'] == 304:
                    continue

                errors[file_download_result['container']] += 1

    return sorted(
        FailedContainer(name, number_of_failures)
        for name, number_of_failures in errors.items()
    )


def create_swift_container(container_name, **kwargs):
    """
    Create a Swift container with publicly readable objects (given the URL).
    """
    with swift_service(**kwargs) as service:
        service.post(container_name, options={'read_acl': '.r:*'})


def delete_swift_container(container_name, **kwargs):
    """
    Delete a Swift container.
    """
    with swift_service(**kwargs) as service:
        # Service delete may yield arbitrary large amount of results,
        # and since it yields we should read all results.
        for result in service.delete(container_name):  # pylint: disable=unused-variable
            pass
