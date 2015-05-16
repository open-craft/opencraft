
# Imports #####################################################################

from django.shortcuts import get_object_or_404, render

from .models import Task


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

def detail(request, task_id):
    context = get_context()
    context['task'] = get_object_or_404(Task, pk=task_id)

    return render(request, 'task/detail.html', context)
