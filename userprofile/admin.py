# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Admin for the userprofile app
"""

# Imports #####################################################################
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from userprofile.models import UserProfile, Organization


# ModelAdmins #################################################################

class UserProfileInline(admin.TabularInline):  # pylint: disable=missing-docstring
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'


class UserAdmin(BaseUserAdmin):  # pylint: disable=missing-docstring
    inlines = (UserProfileInline,)


class OrganizationAdmin(admin.ModelAdmin):  # pylint: disable=missing-docstring
    list_display = (
        'github_handle',
        'account_actions',
    )

    def account_actions(self, obj):
        """
        This method will extract actions in the admin panel for each record. Currently
        the only action we're generating is a link to the report.
        :param obj: The instance we this action is related to
        :return: An HTML of the actions we want to display.
        """
        now = timezone.now()

        if obj and obj.github_handle:
            return format_html(
                '<a class="button" target="_blank" href="{}">Invoice Report</a>',
                reverse('reports:report', kwargs={
                    'organization': obj.github_handle,
                    'year': now.year,
                    'month': now.month
                }),
            )

    account_actions.short_description = 'Account Actions'
    account_actions.allow_tags = True


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Organization, OrganizationAdmin)
