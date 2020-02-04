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
Contants used by the V2 API enpoints.
"""

NO_STATUS = 'NO_STATUS'
PREPARING_INSTANCE = 'PREPARING_INSTANCE'
PENDING_CHANGES = 'PENDING_CHANGES'
UP_TO_DATE = 'UP_TO_DATE'
DEPLOYING = 'DEPLOYING'

DEPLOYMENT_STATUS_CHOICES = (
    (NO_STATUS, NO_STATUS),
    (PREPARING_INSTANCE, PREPARING_INSTANCE),
    (PENDING_CHANGES, PENDING_CHANGES),
    (UP_TO_DATE, UP_TO_DATE),
    (DEPLOYING, DEPLOYING),
)
