"""
Admin for the instance app
"""

#pylint: disable=no-init


# Imports #####################################################################

from django.contrib import admin
from .models import InstanceLogEntry, OpenStackServer, OpenEdXInstance, ServerLogEntry


# ModelAdmins #################################################################

class InstanceLogEntryAdmin(admin.ModelAdmin):
    list_display = ('instance', 'created', 'level', 'text', 'modified')

class OpenStackServerAdmin(admin.ModelAdmin):
    list_display = ('openstack_id', 'status', 'instance', 'created', 'modified')

class OpenEdXInstanceAdmin(admin.ModelAdmin):
    list_display = ('sub_domain', 'base_domain', 'name', 'created', 'modified')

class ServerLogEntryAdmin(admin.ModelAdmin):
    list_display = ('instance', 'server', 'created', 'level', 'text', 'modified')

admin.site.register(InstanceLogEntry, InstanceLogEntryAdmin)
admin.site.register(OpenStackServer, OpenStackServerAdmin)
admin.site.register(OpenEdXInstance, OpenEdXInstanceAdmin)
admin.site.register(ServerLogEntry, ServerLogEntryAdmin)
