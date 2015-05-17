"""
User models serializers (API representation)
"""

#pylint: disable=no-init

from rest_framework import serializers

from task.serializers import ProjectSerializer
from .models import Organization

class OrganizationSerializer(serializers.ModelSerializer):
    pk = serializers.HyperlinkedIdentityField(view_name='api:organization-detail')
    project_set = ProjectSerializer(many=True, read_only=True)

    class Meta:
        model = Organization
        fields = ('pk', 'name', 'project_set', 'created', 'modified')
