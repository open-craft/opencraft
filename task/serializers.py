"""
Task serializers (API representation)
"""

#pylint: disable=no-init

from rest_framework import serializers

from .models import Project, Task

class ProjectSerializer(serializers.HyperlinkedModelSerializer):
    organization = serializers.HyperlinkedRelatedField(view_name='api:organization-detail', read_only=True)

    class Meta:
        model = Project
        fields = ('title', 'organization', 'description', 'created', 'modified')

class TaskSerializer(serializers.HyperlinkedModelSerializer):
    project = serializers.HyperlinkedRelatedField(view_name='api:project-detail', read_only=True)

    class Meta:
        model = Task
        fields = ('title', 'project', 'description', 'created', 'modified')
