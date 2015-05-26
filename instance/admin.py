"""
Admin for the instance app
"""

#pylint: disable=no-init


# Imports #####################################################################

from django.contrib import admin
from .models import OpenStackServer, OpenEdXInstance


# ModelAdmins #################################################################

class OpenStackServerAdmin(admin.ModelAdmin):
    list_display = ('openstack_id', 'status', 'instance', 'created', 'modified')

class OpenEdXInstanceAdmin(admin.ModelAdmin):
    list_display = ('sub_domain', 'base_domain', 'name', 'created', 'modified')

admin.site.register(OpenStackServer, OpenStackServerAdmin)
admin.site.register(OpenEdXInstance, OpenEdXInstanceAdmin)
