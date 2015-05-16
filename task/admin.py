"""
Admin for the task app
"""

#pylint: disable=no-init

from django.contrib import admin
from .models import Task

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'created', 'modified')

admin.site.register(Task, TaskAdmin)
