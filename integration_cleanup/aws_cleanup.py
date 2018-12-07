import boto3

class AwsCleanupInstance:
    """
    Handles the cleanup of IAM users, Policies and Buckets related to CircleCI
    """
    def __init__(self, age_limit, aws_access_key_id, aws_secret_access_key,
                 policy_name, dry_run=False):
        """
        Set's up AWS connections and clients
        """
        self.age_limit = age_limit
        self.dry_run = dry_run
        self.policy_name = policy_name

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
        if not self.dry_run:
            print("Deleting bucket {}.".format(bucket_name))
            bucket = self.s3_resource.Bucket(bucket_name)
            bucket.objects.all().delete()
            bucket.delete()
        else:
            print("DRY_RUN: Deleting bucket {}.".format(bucket_name))

    def delete_user_policy(self, username, policy_name):
        """
        Deletes policy associated to user
        """
        if not self.dry_run:
            print("Deleting policy {} from user {}.".format(policy_name, username))
            self.iam_client.delete_user_policy(
                UserName=username,
                PolicyName=policy_name
            )
        else:
            print("DRY_RUN: Deleting policy {} from user {}.".format(policy_name, username))

    def delete_user_access_key(self, username, access_key):
        """
        Deletes a user's access key
        """
        if not self.dry_run:
            print("Deleting access key {}  from user {}.".format(
                access_key,
                username
            ))
            self.iam_client.delete_access_key(
                UserName=username,
                AccessKeyId=access_key['AccessKeyId']
            )
        else:
            print("DRY_RUN: Deleting access key {}  from user {}.".format(
                access_key,
                username
            ))

    def delete_user(self, username):
        """
        Deletes a IAM user
        """
        if not self.dry_run:
            print("Deleting user {}.".format(username))
            self.iam_client.delete_user(UserName=username)
        else:
            print("DRY_RUN: Deleting user {}.".format(username))

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

    def get_iam_user_access_keys(self, username):
        """
        Lists alls of an user access keys
        """
        user_access_keys = []
        paginator = self.iam_client.get_paginator('list_access_keys')
        for page in paginator.paginate(UserName=username):
            for access_key in page['AccessKeyMetadata']:
                user_access_keys.append(access_key)
        return user_access_keys

    def get_iam_user_old_access_keys(self, username):
        """
        Lists all IAM user access keys and returns only the ones that haven't
        been used in at least age_limit
        [
            {
                'UserName': 'string',
                'AccessKeyId': 'string',
                'Status': 'Active'|'Inactive',
                'CreateDate': datetime(2015, 1, 1)
            },
            {
                'UserName': 'string',
                'AccessKeyId': 'string',
                'Status': 'Active'|'Inactive',
                'CreateDate': datetime(2015, 1, 1)
            },
        ]
        """
        old_keys = []
        user_access_keys = self.get_iam_user_access_keys(username)
        for access_key in user_access_keys:
            # Get last_used date of user key
            last_used = self.iam_client.get_access_key_last_used(AccessKeyId=access_key['AccessKeyId'])
            last_used_date = last_used.get('AccessKeyLastUsed', {}).get('LastUsedDate')

            if last_used_date and (last_used_date < self.age_limit):
                old_keys.append(access_key)

        return old_keys

    def get_iam_user_policy(self, username, policy_name):
        """
        Retrieves IAM user policy, if it exists
        """
        return self.iam_client.get_user_policy(
            UserName=username,
            PolicyName=policy_name
        )

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
        # Iterates over all IAM users
        for user in self.get_iam_users():
            old_keys = self.get_iam_user_old_access_keys(
                username=user['UserName']
            )
            # If the user has any old keys, proceed with deletion
            if old_keys:
                user_policy = self.get_iam_user_policy(
                    user['UserName'],
                    self.policy_name
                )
                # If user policy exists
                if user_policy:
                    buckets_to_delete = self.get_bucket_names_from_policy(user_policy)

                    # Delete buckets, user policy, access keys and the iam user
                    for bucket_name in buckets_to_delete:
                        self.delete_bucket(bucket_name)

                    self.delete_user_policy(user['UserName'], self.policy_name)

                    for access_key in old_keys:
                        self.delete_user_access_key(
                            username=user['UserName'],
                            access_key=access_key
                        )
                    self.delete_user(username=user['UserName'])
