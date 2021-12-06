# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <contact@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
The admin site registration for the Grove app.
"""

from django.contrib import admin

from grove.models.deployment import GroveDeployment
from grove.models.instance import GroveInstance
from grove.models.repository import GroveClusterRepository
from instance.admin import InlineInstanceReferenceAdmin


class GroveClusterRepositoryAdmin(admin.ModelAdmin):  # pylint: disable=missing-docstring
    list_display = ("name", "project_id", "unleash_instance_id", "git_ref",)
    list_filter = ("project_id",)
    search_fields = ("name",)


class GroveDeploymentAdmin(admin.ModelAdmin):  # pylint: disable=missing-docstring
    list_display = ("instance", "creator", "type", "has_overrides", "created")
    list_filter = ("creator", "type", "created")

    def has_overrides(self, obj):
        """
        Return whether deployment includes any changes.
        """
        return bool(obj.overrides)


class GroveInstanceAdmin(admin.ModelAdmin):  # pylint: disable=missing-docstring
    list_display = ('repository', 'name', 'created', 'modified',)
    search_fields = ('internal_lms_domain',)
    inlines = (
        InlineInstanceReferenceAdmin,
    )

    def get_inline_instances(self, request, obj=None):
        """
        Hides inlines while creating ``GroveInstance``.
        """
        # Doesn't show the inline instance for new objects since we have custom
        # logic for creating InstanceReference objects
        if obj is None or obj.pk is None:
            return []
        return super().get_inline_instances(request, obj)


admin.site.register(GroveClusterRepository, GroveClusterRepositoryAdmin)
admin.site.register(GroveDeployment, GroveDeploymentAdmin)
admin.site.register(GroveInstance, GroveInstanceAdmin)
