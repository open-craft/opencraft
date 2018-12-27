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
PR Watcher API
"""

# Imports #####################################################################

from rest_framework import viewsets, serializers, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from pr_watch import github
from pr_watch.filters import IsOrganizationOwnerFilterBackendWatchedPR
from pr_watch.models import WatchedPullRequest
from pr_watch.serializers import WatchedPullRequestSerializer


# Views - API #################################################################


class WatchedPullRequestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API to update instances from their PR
    """
    queryset = WatchedPullRequest.objects.all()
    serializer_class = WatchedPullRequestSerializer
    filter_backends = (IsOrganizationOwnerFilterBackendWatchedPR,)

    @detail_route(methods=['post'])
    def update_instance(self, request, pk):
        """
        Update the instance associated with this PR, creating it if necessary.

        This will update the instance's settings, but will not provision a new AppServer.
        """
        obj = self.get_object()
        # TODO: Make update_from_pr() fetch the PR, rather than us having to do it first, then
        # that method making a redundant second call to fetch the branch tip.
        pr = github.get_pr_by_number(obj.target_fork_name, obj.github_pr_number)
        try:
            obj.update_instance_from_pr(pr)
        except github.ObjectDoesNotExist:
            # The branch has been deleted from GitHub. This exception won't be needed once the
            # refactor mentioned above is implemented.
            return Response(
                {'error': 'Could not fetch updated details from GitHub.'}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response({'status': 'Instance updated.'})

    def get_serializer_class(self):
        """
        Fix the form shown in the API browser for /pr_watch/:id/update_instance/
        """
        if self.action == 'update_instance':
            return serializers.Serializer
        return self.serializer_class
