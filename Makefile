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

# Config ######################################################################

WORKERS = 4
SHELL = /bin/bash


# Parameters ##################################################################

# For `test_one` use the rest as arguments and turn them into do-nothing targets
ifeq (test_one,$(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif


# Commands ####################################################################

all:
	rundev

clean:
	find -name '*.pyc' -delete
	find -name '*~' -delete
	find -name '__pycache__' -type d -delete
	rm -rf .coverage build
	find static/js/external -type f -not -name 'Makefile' -not -name '.gitignore' -delete

collectstatic: clean js_external
	honcho run ./manage.py collectstatic --noinput

migrate: clean
	honcho run ./manage.py migrate

migration_check: clean
	!((honcho run ./manage.py showmigrations | grep '\[ \]') && printf "\n\033[0;31mERROR: Pending migrations found\033[0m\n\n")

migration_autogen: clean
	honcho run ./manage.py makemigrations

run: clean migration_check collectstatic
	honcho start --concurrency "worker=$(WORKERS)"

rundev: clean migration_check js_external
	honcho start -f Procfile.dev

shell:
	honcho run ./manage.py shell_plus

upgrade_dependencies:
	pip freeze --local | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U


# Tests #######################################################################

test_prospector: clean
	prospector --profile opencraft

test_unit: clean
	honcho -e .env.test run coverage run --source='.' --omit='*/tests/*' ./manage.py test --noinput
	coverage html
	@echo -e "\nCoverage HTML report at file://`pwd`/build/coverage/index.html\n"
	@coverage report --fail-under 94 || (echo "\nERROR: Coverage is below 95%\n" && exit 2)

test_integration: clean
	@if [ -a .env.integration ] ; then \
		echo -e "\nRunning integration tests..." ; \
		honcho -e .env.integration run ./manage.py test --pattern=integration_*.py --noinput ; \
	else \
		echo -e "\nIntegration tests skipped (create a '.env.integration' file to run them)" ; \
	fi

test_js: clean js_external
	cd instance/tests/js && jasmine-ci --logs --browser firefox

test_js_web: clean js_external
	cd instance/tests/js && jasmine --host 0.0.0.0

test: clean test_prospector test_unit test_js test_integration
	@echo -e "\nAll tests OK!\n"

test_one: clean
	honcho -e .env.test run ./manage.py test $(RUN_ARGS)


# Files #######################################################################

js_external:
	$(MAKE) -C static/js/external
