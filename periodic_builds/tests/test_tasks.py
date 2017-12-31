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
Worker tasks - Tests
"""

# Imports #####################################################################

import textwrap
from unittest.mock import patch
import yaml

from django.test import TestCase, override_settings

from instance.models.openedx_instance import OpenEdXInstance
from pr_watch import tasks
from pr_watch.github import RateLimitExceeded
from pr_watch.models import WatchedPullRequest
from pr_watch.tests.factories import WatchedForkFactory, PRFactory


# Tests #######################################################################

raise NotImplementedError("FIXME write tests, similar to the ones in pr_watch")

