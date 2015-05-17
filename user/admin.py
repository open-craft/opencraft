"""
Admin for the user app
"""

#pylint: disable=no-init


# Imports #####################################################################

from django.contrib import admin
from .models import Organization


# ModelAdmins #################################################################

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'modified')

admin.site.register(Organization, OrganizationAdmin)
