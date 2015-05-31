"""
Instance serializers (API representation)
"""

#pylint: disable=no-init

from rest_framework import serializers

from .models import OpenStackServer, OpenEdXInstance

class OpenStackServerSerializer(serializers.ModelSerializer):
    pk_url = serializers.HyperlinkedIdentityField(view_name='api:openstackserver-detail')
    instance = serializers.HyperlinkedRelatedField(view_name='api:openedxinstance-detail', read_only=True)

    class Meta:
        model = OpenStackServer
        fields = ('pk', 'pk_url', 'status', 'instance', 'openstack_id', 'created', 'modified')

class OpenEdXInstanceSerializer(serializers.ModelSerializer):
    pk_url = serializers.HyperlinkedIdentityField(view_name='api:openedxinstance-detail')
    server_set = OpenStackServerSerializer(many=True, read_only=True)

    class Meta:
        model = OpenEdXInstance
        fields = ('pk', 'pk_url', 'server_set', 'sub_domain', 'base_domain', 'email', 'name', 'protocol',
                  'domain', 'url', 'branch_name', 'commit_id', 'github_organization_name',
                  'github_organization_name', 'github_base_url', 'log_text', 'repository_url', 'updates_feed',
                  'vars_str', 'created', 'modified')
