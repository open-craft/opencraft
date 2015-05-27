
# Imports #####################################################################

from django.shortcuts import render
from rest_framework import viewsets

from .models import Project, Task
from .serializers import ProjectSerializer, TaskSerializer


# Functions - Helpers #########################################################

def get_context():
    task_list = Task.objects.order_by('-created')

    context = {
        'task_list': task_list,
    }

    return context


# Views #######################################################################

def index(request):
    return render(request, 'task/index.html', get_context())


# Views - API #################################################################

class ProjectViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class TaskViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
