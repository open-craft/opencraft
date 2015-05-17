"""
Admin for the task app
"""

#pylint: disable=no-init


# Imports #####################################################################

from django.contrib import admin
from .models import Project, Task


# ModelAdmins #################################################################

class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'organization', 'created', 'modified')

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'created', 'modified')

admin.site.register(Project, ProjectAdmin)
admin.site.register(Task, TaskAdmin)
