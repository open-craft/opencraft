# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
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
Admin for the registration app
"""

# Imports #####################################################################

from django.contrib import admin

from registration.models import BetaTestApplication


# ModelAdmins #################################################################

class BetaTestApplicationAdmin(admin.ModelAdmin): #pylint: disable=missing-docstring
    list_display = ('user', 'domain', 'instance_name', 'public_contact_email',
                    'status', 'first_activated', 'created')
    list_filter = ('status', 'subscribe_to_updates')
    search_fields = ('user__username', 'subdomain', 'instance_name',
                     'public_contact_email')
    date_hierarchy = 'created'


admin.site.register(BetaTestApplication, BetaTestApplicationAdmin)
