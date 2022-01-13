# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <contact@opencraft.com>
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

from instance.models.openedx_instance import OpenEdXInstance
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

    def get_filtered_queryset(self, queryset, organization):
        """
        Return filtered queryset by organization.
        """
        return queryset.filter(owner__owner=organization)


class IsOrganizationOwnerFilterBackendInstance(IsOrganizationOwnerFilterBackend):
    """
    Filter for Instance.
    """

    def get_filtered_queryset(self, queryset, organization):
        """
        Return filtered queryset by organization.
        """
        return queryset.filter(owner=organization)


class InstanceFilterBackend(filters.BaseFilterBackend):
    """
    More complex filter for Instance that allows users to filter on fields.

    Currently allowed fields:
    - deployment_type
    - name
    - notes
    - openedx_release
    - status
    - tag
    """

    def _filter_name(self, queryset, value):
        if value:
            return queryset.filter(name__icontains=value)
        return queryset

    def _filter_notes(self, queryset, value):
        if value:
            return queryset.filter(notes__icontains=value)
        return queryset

    def _filter_status(self, queryset, value):
        if value:
            # The .distinct is important, because an instance reference can
            # have multiple appservers with the same status. In that case
            # there'll be duplicate rows.
            return queryset.filter(openedxappserver_set___status=value).distinct()
        return queryset


    def _filter_openedx_release(self, queryset, value):
        if value:
            instances = OpenEdXInstance.objects.filter(openedx_release__iexact=value)
            return queryset.filter(instance_id__in=instances)
        return queryset

    def _filter_tag(self, queryset, value):
        if value:
            instances = OpenEdXInstance.objects.filter(tags__name__endswith=value)
            return queryset.filter(instance_id__in=instances)
        return queryset

    def _filter_deployment_type(self, queryset, value):
        if value:
            return queryset.filter(deployment__type=value)
        return queryset

    def filter_queryset(self, request, queryset, view):
        """
        Filters the queryset.

        For each field in request.GET looks for a corresponding self._filter_{field}
        method to filter by.
        """
        # Note: This method was done for simplicity. It would be more advantageous to add
        # django_filters once filtering gets more complex.
        for field, value in request.query_params.items():
            try:
                filter_func = getattr(self, f'_filter_{field}')
            except AttributeError:
                continue

            queryset = filter_func(queryset, value)
        return queryset
