# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
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
Filters for the API
"""

from rest_framework import filters

from userprofile.models import UserProfile


class IsOrganizationOwnerFilterBackend(filters.BaseFilterBackend):
    """
    Filter that only allows user to see objects of the same organization. Admins still see all objects.
    This class checks the permissions logic.
    Each subclass implements the logic of which particular fields to use to do the filtering (e.g. filter
    instances, filter appservers, filter PRs, etc.)
    """

    def filter_queryset(self, request, queryset, view):
        if request.user.is_superuser:
            return queryset
        userprofile = UserProfile.objects.get(user=request.user)
        organization = userprofile.organization
        if request.user.has_perm("instance.manage_own") and organization:
            return self.get_filtered_queryset(queryset, organization)
        return queryset.none()


class IsOrganizationOwnerFilterBackendAppServer(IsOrganizationOwnerFilterBackend):
    """
    Filter for Appserver.
    """

    def get_filtered_queryset(self, queryset, organization):  # pylint: disable=no-self-use
        """
        Return filtered queryset by organization.
        """
        return queryset.filter(owner__owner=organization)


class IsOrganizationOwnerFilterBackendInstance(IsOrganizationOwnerFilterBackend):
    """
    Filter for Instance.
    """

    def get_filtered_queryset(self, queryset, organization):  # pylint: disable=no-self-use
        """
        Return filtered queryset by organization.
        """
        return queryset.filter(owner=organization)
