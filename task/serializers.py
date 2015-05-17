"""
Task serializers (API representation)
"""

#pylint: disable=no-init

from rest_framework import serializers

from .models import Project, Task

class TaskSerializer(serializers.ModelSerializer):
    pk = serializers.HyperlinkedIdentityField(view_name='api:task-detail')
    project = serializers.HyperlinkedRelatedField(view_name='api:project-detail', read_only=True)

    class Meta:
        model = Task
        fields = ('pk', 'title', 'project', 'description', 'created', 'modified')

class ProjectSerializer(serializers.ModelSerializer):
    pk = serializers.HyperlinkedIdentityField(view_name='api:project-detail')
    task_set = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ('pk', 'title', 'task_set', 'description', 'created', 'modified')
