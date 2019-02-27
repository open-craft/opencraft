"""
Helper functions to stub botocore requests in unit tests
"""

import json

from botocore.stub import Stubber

from instance.models.mixins import storage


class S3Stubber(Stubber):
    """
    Helper class to simplify stubbing S3 operations
    """

    def stub_create_bucket(self, bucket='test', location='test'):
        """ Stub helper for 'create_bucket' """
        if not location or location == 'us-east-1':
            expected_params = {
                'Bucket': bucket
            }
        else:
            expected_params = {
                'Bucket': bucket, 'CreateBucketConfiguration': {
                    'LocationConstraint': location
                }
            }
        self.add_response('create_bucket', {
            'Location': location
        }, expected_params)

    def stub_put_cors(self, bucket='test'):
        """ Stub helper for 'put_bucket_cors' """
        self.add_response('put_bucket_cors', {}, {
            'Bucket': bucket,
            'CORSConfiguration': {
                'CORSRules': [{
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['GET', 'PUT']
                }]
            }
        })

    def stub_set_expiration(self, bucket='test', days=30, prefix=''):
        """ Stub helper for 'put_bucket_lifecycle_configuration' """
        self.add_response('put_bucket_lifecycle_configuration', {}, {
            'Bucket': bucket,
            'LifecycleConfiguration': {
                'Rules': [
                    {
                        'NoncurrentVersionExpiration': {
                            'NoncurrentDays': days
                        },
                        'Prefix': prefix,
                        'Status': 'Enabled',
                    },
                ]
            }
        })

    def stub_versioning(self, bucket='test', status='Enabled'):
        """ Stub helper for 'put_bucket_versioning' """
        self.add_response('put_bucket_versioning', {}, {
            'Bucket': bucket,
            'VersioningConfiguration': {
                'Status': status
            }
        })

    def stub_put_object(self, body, key, bucket='test'):
        """ Stub helper for 'put_object' """
        self.add_response('put_object', {}, {
            'Bucket': bucket,
            'Body': body,
            'Key': key
        })

    def stub_delete_object(self, key, version_id=None, bucket='test'):
        """ Stub helper for 'delete_object' """
        if version_id is None:
            self.add_response('delete_object', {}, {
                'Bucket': bucket,
                'Key': key
            })
        else:
            self.add_response('delete_object', {}, {
                'Bucket': bucket,
                'Key': key,
                'VersionId': version_id
            })

    def stub_list_object_versions(self, result, bucket='test'):
        """ Stub helper for 'list_object_versions' """
        self.add_response('list_object_versions', result, {
            'Bucket': bucket
        })

    def stub_delete_bucket(self, bucket='test'):
        """ Stub helper for 'delete_bucket' """
        self.add_response('delete_bucket', {}, {
            'Bucket': bucket
        })


class IAMStubber(Stubber):
    """
    Helper class to simplify stubbing IAM operations
    """

    def stub_create_user(self, username):
        """ Stub helper for 'create_user' """
        self.add_response('create_user', {}, {
            'UserName': username
        })

    def stub_put_user_policy(self, username, policy_name, policy_document):
        """ Stub helper for 'put_user_policy' """
        self.add_response('put_user_policy', {}, {
            'UserName': username,
            'PolicyName': policy_name,
            'PolicyDocument': json.dumps(policy_document)
        })

    def stub_create_access_key(self, username, access_key='test_0123456789a', secret='secret'):
        """ Stub helper for 'create_access_key' """
        self.add_response('create_access_key', service_response={
            'AccessKey': {
                'UserName': username,
                'AccessKeyId': access_key,
                'SecretAccessKey': secret,
                'Status': 'Active'
            }
        }, expected_params={
            'UserName': username
        })

    def stub_delete_access_key(self, username, access_key_id):
        """ Stub helper for 'delete_access_key' """
        self.add_response('delete_access_key', {}, {
            'UserName': username,
            'AccessKeyId': access_key_id
        })

    def stub_delete_user_policy(self, username, policy_name=storage.USER_POLICY_NAME):
        """ Stub helper for 'delete_user_policy' """
        self.add_response('delete_user_policy', {}, {
            'UserName': username,
            'PolicyName': policy_name
        })

    def stub_delete_user(self, username):
        """ Stub helper for 'delete_user' """
        self.add_response('delete_user', {}, {
            'UserName': username
        })
