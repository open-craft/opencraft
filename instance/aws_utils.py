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
AWS - Helper functions
"""

# Imports #####################################################################
import logging

from django.conf import settings
import boto3
from botocore.exceptions import ClientError


# Logging #####################################################################

logger = logging.getLogger(__name__)

# Functions ###################################################################

def get_boto3_session():
    """
    Open an authenticated boto3 AWS session.

    Credentials are pulled from the settings.
    """
    session = boto3.session.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return session


def create_servers(boto_session, server_name, key_name,
                   security_group_names=None,
                   region_name=None,
                   instance_type=None,
                   ami_id=None,
                   num_servers=1,
):
    """
    Create EC2 VM(s) via boto3

    Returns a list of created ec2.Instance objects.
    """
    if not region_name:
        region_name = settings.AWS_DEFAULT_REGION

    if not instance_type:
        instance_type = settings.AWS_INSTANCE_TYPE

    if not ami_id:
        ami_id = settings.AWS_INSTANCE_MACHINE_IMAGE_ID

    storage_blocks = [
        {"DeviceName": "/dev/sda1", "Ebs" : {"VolumeSize" : settings.AWS_INSTANCE_VOLUME_SIZE}},
    ]

    security_groups = []
    if security_group_names:
        for security_group_name in security_group_names:
            security_group_id = get_security_group_id(boto_session, security_group_name, create=False)
            if security_group_id:
                security_groups.append(security_group_id)

    ec2_resource = boto_session.resource('ec2')

    # Create the EC2 instance(s) in the default VPC
    logger.info('Creating %s AWS EC2 server(s): name=%s ami=%s type=%s', num_servers, server_name, ami_id, instance_type)
    ec2_instances = ec2_resource.create_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        BlockDeviceMappings=storage_blocks,
        MinCount=1,
        MaxCount=num_servers,
        SecurityGroupIds=security_groups,
    )

    # Name the created instances
    ec2_resource.create_tags(
        Resources=[instance.id for instance in ec2_instances],
        Tags=[dict(Key='Name', Value=server_name)]
    )

    return ec2_instances


def get_ec2_instance(boto_session, instance_id):
    """
    Returns the ec2.Instance object for the given Id.
    """
    ec2_resource = boto_session.resource('ec2')
    instances = ec2_resource.instances.filter(InstanceIds=[instance_id])
    for instance in instances:
        return instance
    return None


def get_ec2_instance_public_ip(boto_session, instance_id):
    """
    Returns the public IP address for the given EC2 instance Id.

    Returns None if not found.
    """
    instance = get_ec2_instance(boto_session, instance_id)
    if instance:
        return instance.public_ip_address
    return None


def get_ec2_instance_state(boto_session, instance_id):
    """
    Returns the State string for the given EC2 instance Id, e.g. 'running', 'stopped', 'terminated'

    Returns None if not found.
    """
    instance = get_ec2_instance(boto_session, instance_id)
    if instance:
        return instance.state.get('Name')
    return None


def _get_ec2_instance_status_check(boto_session, instance_id):
    """
    Returns the status details for the given EC2 instance Id.

    Returns None if not found.
    """
    client = boto_session.client('ec2')
    all_statuses = client.describe_instance_status(InstanceIds=[instance_id])
    for details in all_statuses.get('InstanceStatuses', []):
        if details.get('InstanceId', '') == instance_id:
            return details
    return None


def get_ec2_instance_status(boto_session, instance_id):
    """
    Returns the status string for the given EC2 instance Id.

    Returns None if not found.
    """
    status_details = _get_ec2_instance_status_check(boto_session, instance_id)
    if status_details:
        return status_details.get('InstanceStatus', {}).get('Status')
    else:
        return get_ec2_instance_state(boto_session, instance_id)
    return None


def get_default_vpc_id(boto_session):
    """
    Return the default VPC instance
    """
    ec2_client = boto_session.client('ec2')
    response = ec2_client.describe_vpcs()
    for vpc in response.get('Vpcs', []):
        if vpc.get('IsDefault', False):
            return vpc.id
    return None


def get_security_group_id(boto_session, name, create=False):
    """
    Return the SecurityGroupId with the given name.

    Create one if not found, and create==True.
    """
    ec2_client = boto_session.client('ec2')
    group_id = None
    try:
        response = ec2_client.describe_security_groups(GroupNames=[name])
        group_id = response.get('SecurityGroups', [{}])[0].get('GroupId')
    except ClientError as err:
        logger.debug('AWS SecurityGroup with name=%s not found: %s', name, err)

    if create and not group_id:
        try:
            vpc_id = get_default_vpc_id(boto_session)
            response = ec2_client.create_security_group(GroupName=name, Description=name, VpcId=vpc_id)
            group_id = response.get('GroupId')
        except ClientError as err:
            logger.debug('Unable to create AWS SecurityGroup with name=%s, vpc_id=%s: %s', name, vpc_id, err)

    return group_id
