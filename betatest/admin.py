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
Admin for the betatest app
"""

# Imports #####################################################################

from django.contrib import admin

from betatest.models import BetaTestApplication


# ModelAdmins #################################################################

class BetaTestApplicationAdmin(admin.ModelAdmin): #pylint: disable=missing-docstring
    list_display = ('user', 'domain')


admin.site.register(BetaTestApplication, BetaTestApplicationAdmin)
