"""
Task serializers (API representation)
"""

#pylint: disable=no-init

from rest_framework import serializers
from .models import Task

class TaskSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Task
        fields = ('title', 'description', 'created', 'modified')
