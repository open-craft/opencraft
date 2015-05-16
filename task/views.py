from django.shortcuts import get_object_or_404, render

from .models import Task


def index(request):
    task_list = Task.objects.order_by('-created')

    context = {'task_list': task_list}

    return render(request, 'task/index.html', context)

def detail(request, task_id):
    task = get_object_or_404(Task, pk=task_id)

    context = {'task': task}

    return render(request, 'task/detail.html', context)
