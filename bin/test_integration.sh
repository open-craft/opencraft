#!/usr/bin/env bash
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

# Integration tests script ####################################################
#
# Do not run manually - use `make test_integration` from the root directory

# Check if integration tests are configured
if [ ! -f .env.integration ] ; then
    echo -e "\nIntegration tests skipped (create a '.env.integration' file to run them)"
    exit 0
else
    echo -e "\nRunning integration tests..."
fi

# Heartbeat - ensure we output something every 5 minutes, until the script ends
# This is useful for avoiding tools like CircleCI to think the process is crashed during long operations
trap 'kill $(jobs -p)' EXIT
while [ 0 ]; do echo -e "\n== BEAT: `date --iso-8601=seconds` ==\n" ; sleep 300 ; done &

honcho -e .env.integration run ./manage.py test --pattern=integration_*.py --noinput
