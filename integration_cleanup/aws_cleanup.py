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
S3 Cleanup Script

Cleans up all AWS IAM Users, Policies, Access Keys and Buckets
"""

import boto3
import logging


# Constants ###################################################################

DEFAULT_POLICY_NAME = "allow_access_s3_bucket"


# Logging #####################################################################

logger = logging.getLogger('integration_cleanup')


# Classes #####################################################################

class AwsCleanupInstance:
    """
    Handles the cleanup of IAM users, Policies and Buckets related to CircleCI
    """
    def __init__(self, age_limit, aws_access_key_id, aws_secret_access_key, dry_run=False):
        """
        Set's up AWS connections and clients
        """
        self.age_limit = age_limit
        self.dry_run = dry_run
        self.cleaned_up_hashes = []

        self.session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.iam_client = self.session.client('iam')
        self.s3_client = self.session.client('s3')
        self.s3_resource = self.session.resource('s3')

    def delete_bucket(self, bucket_name):
        """
        Deletes a S3 bucket and all of it's files
        """
        if self.dry_run:
            return
        try:
            logger.info("Deleting bucket {}.".format(bucket_name))
            bucket = self.s3_resource.Bucket(bucket_name)
            bucket.object_versions.delete()
            bucket.objects.all().delete()
            bucket.delete()
        except self.s3_client.exceptions.NoSuchBucket:
            # Ignore if the bucket doesn't exist
            pass

    def delete_user_policy(self, username, policy_name):
        """
        Deletes policy associated to user
        """
        if self.dry_run:
            return
        self.iam_client.delete_user_policy(
            UserName=username,
            PolicyName=policy_name
        )

    def delete_user_access_key(self, username, access_key):
        """
        Deletes a user's access key
        """
        if self.dry_run:
            return
        self.iam_client.delete_access_key(
            UserName=username,
            AccessKeyId=access_key['AccessKeyId']
        )

    def delete_user(self, username):
        """
        Deletes a IAM user
        """
        if self.dry_run:
            return
        self.iam_client.delete_user(UserName=username)

    def get_iam_users(self):
        """
        Lists all IAM users
        """
        users = []
        paginator = self.iam_client.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                users.append(user)
        return users

    def get_iam_user_old_access_keys(self, username):
        """
        Lists all IAM user access keys and returns only the ones that haven't
        been used in at least age_limit
        """
        old_keys = []
        user_access_keys = []

        # Get all user access keys
        paginator = self.iam_client.get_paginator('list_access_keys')
        for page in paginator.paginate(UserName=username):
            for access_key in page['AccessKeyMetadata']:
                user_access_keys.append(access_key)

        # Check when last used and return only oldest ones
        for access_key in user_access_keys:
            # Get last_used date of user key
            last_used = self.iam_client.get_access_key_last_used(AccessKeyId=access_key['AccessKeyId'])
            last_used_date = last_used.get('AccessKeyLastUsed', {}).get('LastUsedDate')

            if last_used_date and (last_used_date < self.age_limit):
                old_keys.append(access_key)

        return old_keys

    @staticmethod
    def get_bucket_names_from_policy(policy):
        """
        Lists all bucket names related to a policy
        """
        bucket_names = []
        if policy:
            for statement in policy.get('PolicyDocument', {}).get('Statement', []):
                for action in statement.get('Action', []):
                    if action == 's3:DeleteBucket':
                        bucket_arn = statement.get('Resource')[0]
                        bucket_name = bucket_arn.split(':')[5]
                        if bucket_name:
                            bucket_names.append(bucket_name)
        return bucket_names

    def run_cleanup(self):
        """
        Runs the cleanup of the AWS buckets, IAM users and their policies
        """
        logger.info("\n --- Starting AWS Cleanup ---")
        if self.dry_run:
            logger.info("Running in DRY_RUN mode, no actions will be taken.")

        # Iterates over all IAM users
        for user in self.get_iam_users():
            # Check if user has 'integration' on name
            if 'integration' not in user['UserName']:
                logger.info("  > Skipping user {} as it's not related to integration...".format(user['UserName']))
                continue

            old_keys = self.get_iam_user_old_access_keys(
                username=user['UserName']
            )
            # If the user has any old keys, proceed with deletion
            if old_keys:
                user_policy = self.iam_client.get_user_policy(
                    UserName=user['UserName'],
                    PolicyName=DEFAULT_POLICY_NAME
                )
                # If user policy exists
                if user_policy:
                    buckets_to_delete = self.get_bucket_names_from_policy(user_policy)

                    logger.info("  > Cleaning up stuff from user {}.".format(user['UserName']))

                    # Delete buckets, user policy, access keys and the iam user
                    for bucket_name in buckets_to_delete:
                        logger.info("    * Deleting bucket {}.".format(bucket_name))
                        self.delete_bucket(bucket_name)

                    logger.info("    * Deleting policy {} from user {}.".format(
                        DEFAULT_POLICY_NAME,
                        user['UserName']
                    ))
                    self.delete_user_policy(user['UserName'], DEFAULT_POLICY_NAME)

                    for access_key in old_keys:
                        logger.info("    * Deleting access key {}  from user {}.".format(
                            access_key['AccessKeyId'],
                            user['UserName']
                        ))
                        self.delete_user_access_key(
                            username=user['UserName'],
                            access_key=access_key
                        )

                    logger.info("    * Deleting user {}.".format(user['UserName']))
                    self.delete_user(username=user['UserName'])

                    # Saves hashes from user name
                    # ocim-HASH_integration_plebia_net.
                    self.cleaned_up_hashes.append(
                        user['UserName'].split('_')[0][5:]
                    )
