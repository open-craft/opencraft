# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2016 OpenCraft <contact@opencraft.com>
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
PR Watcher serializers (API representation)
"""

# Imports #####################################################################

from rest_framework import serializers
from pr_watch.models import WatchedPullRequest


# Serializers #################################################################


class WatchedPullRequestSerializer(serializers.ModelSerializer):
    """
    Simple serializer for WatchedPullRequest
    """
    class Meta:
        model = WatchedPullRequest
        fields = (
            'id',
            'fork_name',
            'target_fork_name',
            'branch_name',
            'github_pr_number',
            'github_pr_url',
        )

    def to_representation(self, obj):
        """
        Add additional fields/data to the output
        """
        output = super().to_representation(obj)
        output['instance_id'] = obj.instance.ref.id  # The API must only expose InstanceReference IDs, not Instance ID
        return output
