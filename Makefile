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

# Config ######################################################################

WORKERS = 4
SHELL = /bin/bash
HONCHO_MANAGE := honcho run python3 manage.py
RUN_JS_TESTS := xvfb-run --auto-servernum jasmine-ci --logs --browser firefox


# Parameters ##################################################################

# For `test_one` use the rest as arguments and turn them into do-nothing targets
ifeq ($(firstword $(MAKECMDGOALS)),$(filter $(firstword $(MAKECMDGOALS)),test_one manage))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif


# Commands ####################################################################

all:
	rundev

apt_get_update:
	sudo apt-get update

clean:
	find -name '*.pyc' -delete
	find -name '*~' -delete
	find -name '__pycache__' -type d -delete
	rm -rf .coverage build
	find static/external -type f -not -name 'Makefile' -not -name '.gitignore' -delete
	find static/external -type d -empty -delete

install_system_db_dependencies: apt_get_update
	sudo -E apt-get install -y `tr -d '\r' < debian_db_packages.lst`

install_system_dependencies: apt_get_update
	sudo -E apt-get install -y `tr -d '\r' < debian_packages.lst`

install_virtualenv_system:
	sudo pip3 install virtualenv

create_db:
	createdb --encoding utf-8 --template template0 opencraft || \
	    echo "Could not create database 'opencraft' - it probably already exists"

collectstatic: clean static_external
	honcho run ./manage.py collectstatic --noinput

manage:
	$(HONCHO_MANAGE) $(RUN_ARGS)

migrate: clean
	$(HONCHO_MANAGE) migrate

# Check for unapplied migrations
migration_check: clean
	!(($(HONCHO_MANAGE) showmigrations | grep '\[ \]') && printf "\n\033[0;31mERROR: Pending migrations found\033[0m\n\n")

migration_autogen: clean
	$(HONCHO_MANAGE) makemigrations

run: clean migration_check collectstatic
	honcho start --concurrency "worker=$(WORKERS)"

rundev: clean migration_check static_external
	honcho start -f Procfile.dev

shell:
	$(HONCHO_MANAGE) shell_plus

upgrade_dependencies:
	pip freeze --local | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U

# Tests #######################################################################

test_prospector: clean
	prospector --profile opencraft

test_unit: clean static_external
	honcho -e .env.test run coverage run --source='.' --omit='*/tests/*' ./manage.py test --noinput
	coverage html
	@echo -e "\nCoverage HTML report at file://`pwd`/build/coverage/index.html\n"
	@coverage report --fail-under 94 || (echo "\nERROR: Coverage is below 94%\n" && exit 2)

# Check whether migrations need to be generated, creating "opencraft" database first if it doesn't exist
test_migrations_missing: clean
	honcho -e .env.test run ./manage.py makemigrations --dry-run --check

test_browser: clean static_external
	@echo -e "\nRunning browser tests..."
	xvfb-run --auto-servernum honcho -e .env.test run ./manage.py test --pattern=browser_*.py --noinput

test_integration: clean
ifneq ($(wildcard .env.integration),)
	echo -e "\nRunning integration tests with credentials from .env.integration file..."
	honcho -e .env.integration run ./manage.py test --pattern=integration_*.py --noinput
else ifdef OPENSTACK_USER
	echo -e "\nRunning integration tests with credentials from environment variables..."
	./manage.py test --pattern=integration_*.py --noinput
else
	echo -e "\nIntegration tests skipped (create a '.env.integration' file to run them)"
endif

test_integration_cleanup: clean
ifneq ($(wildcard .env.integration),)
	echo -e "\nRunning integration test cleanup script with credentials from .env.integration file..."
	honcho -e .env.integration run bin/integration-cleanup
else ifdef OPENSTACK_USER
	echo -e "\nRunning integration test cleanup script with credentials from environment variables..."
	bin/integration-cleanup
else
	echo -e "\nIntegration test cleanup script skipped (create a '.env.integration' file to run them)"
endif

test_js: clean static_external
	cd instance/tests/js && $(RUN_JS_TESTS)
	cd registration/tests/js && $(RUN_JS_TESTS)

test_instance_js_web: clean static_external
	cd instance/tests/js && jasmine --host 0.0.0.0

test_registration_js_web: clean static_external
	cd registration/tests/js && jasmine --host 0.0.0.0

test: clean test_prospector test_unit test_migrations_missing test_js test_browser test_integration
	@echo -e "\nAll tests OK!\n"

test_one: clean
	honcho -e .env.test run ./manage.py test $(RUN_ARGS)


# Files #######################################################################

static_external:
	$(MAKE) -C static/external
