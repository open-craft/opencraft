"""
User models serializers (API representation)
"""

#pylint: disable=no-init

from rest_framework import serializers
from .models import Organization

class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Organization
        fields = ('name', 'created', 'modified')
