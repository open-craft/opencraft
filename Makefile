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

# Config ######################################################################

# Any configuration variable can be overridden with `VARIABLE = VALUE` in a git-ignored `private.mk` file.

.DEFAULT_GOAL := help
HELP_SPACING ?= 30
COVERAGE_THRESHOLD ?= 94
WORKERS ?= 3
WORKERS_LOW_PRIORITY ?= 3
SHELL ?= /bin/bash
HONCHO_MANAGE := honcho run python3 manage.py
HONCHO_MANAGE_TESTS := honcho -e .env.test run python3 manage.py
RUN_JS_TESTS := xvfb-run --auto-servernum jasmine-ci --logs --browser firefox

# Parameters ##################################################################

# For `test.one` use the rest as arguments and turn them into do-nothing targets
ifeq ($(firstword $(MAKECMDGOALS)),$(filter $(firstword $(MAKECMDGOALS)),test.one manage))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif

# Commands ####################################################################

help: ## Display this help message.
	@echo "Please use \`make <target>' where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-$(HELP_SPACING)s\033[0m %s\n", $$1, $$2}'

all: run.dev

clean: ## Remove all temporary files.
	find -name '*.pyc' -delete
	find -name '*~' -delete
	find -name '__pycache__' -type d -delete
	rm -rf .coverage build
	find static/external -type f -not -name 'Makefile' -not -name '.gitignore' -delete
	find static/external -type d -empty -delete

apt_get_update: ## Update system package cache.
	sudo apt-get update

install_system_db_dependencies: apt_get_update ## Install system-level DB dependencies from `debian_db_packages.lst`. Ignores comments.
	sudo -E apt-get install -y `grep -v '^#' debian_db_packages.lst | tr -d '\r'`

install_system_dependencies: apt_get_update ## Install system-level dependencies from `debian_packages.lst`. Ignores comments.
	sudo -E apt-get install -y `grep -v '^#' debian_packages.lst | tr -d '\r'`

create_db: ## Create blanket DBs, i.e. `opencraft`.
	createdb --host 127.0.0.1 --encoding utf-8 --template template0 opencraft || \
	    echo "Could not create database 'opencraft' - it probably already exists"

.PHONY: static
static: clean static_external ## Collect static files for production.
	$(HONCHO_MANAGE) collectstatic --noinput

manage: ## Run a management command.
	$(HONCHO_MANAGE) $(RUN_ARGS)

migrate: clean ## Run migrations.
	$(HONCHO_MANAGE) migrate

migrations.check: clean ## Check for unapplied migrations
	!(($(HONCHO_MANAGE) showmigrations | grep '\[ \]') && printf "\n\033[0;31mERROR: Pending migrations found\033[0m\n\n")

migrations: clean ## Generate migrations.
	$(HONCHO_MANAGE) makemigrations

run: clean migrations.check static ## Run Ocim in a production setting with concurrency.
	honcho start --concurrency "worker=$(WORKERS),worker_low_priority=$(WORKERS_LOW_PRIORITY)"

run.dev: clean migrations.check static_external ## Run the developmental server using `runserver_plus`.
	honcho start -f Procfile.dev

shell: ## Start the power shell.
	HUEY_QUEUE_NAME=opencraft_low_priority $(HONCHO_MANAGE) shell_plus

upgrade_dependencies:
	pip freeze --local | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U

# Tests #######################################################################

test.quality: clean ## Run quality tests.
	prospector --profile opencraft --uses django

test.unit: clean static_external ## Run all unit tests.
	honcho -e .env.test run coverage run --source='.' --omit='*/tests/*,venv/*' ./manage.py test --noinput
	coverage html
	@echo "\nCoverage HTML report at file://`pwd`/build/coverage/index.html\n"
	@coverage report --fail-under $(COVERAGE_THRESHOLD) || (echo "\nERROR: Coverage is below $(COVERAGE_THRESHOLD)%\n" && exit 2)

test.migrations_missing: clean ## Check if migrations are missing.
	@$(HONCHO_MANAGE_TESTS) makemigrations --dry-run --check

test.browser: clean static_external ## Run browser-specific tests.
	@echo -e "\nRunning browser tests..."
	xvfb-run --auto-servernum $(HONCHO_MANAGE_TESTS) test --pattern=browser_*.py --noinput

test.integration: clean ## Run integration tests.
ifneq ($(wildcard .env.integration),)
	echo -e "\nRunning integration tests with credentials from .env.integration file..."
	honcho -e .env.integration run ./manage.py test --pattern=integration_*.py --noinput
else ifdef OPENSTACK_USER
	echo -e "\nRunning integration tests with credentials from environment variables..."
	./manage.py test --pattern=integration_*.py --noinput
else
	echo -e "\nIntegration tests skipped (create a '.env.integration' file to run them)"
endif

test.integration_cleanup: clean ## Run the integration cleanup script.
ifneq ($(wildcard .env.integration),)
	echo -e "\nRunning integration test cleanup script with credentials from .env.integration file..."
	honcho -e .env.integration run bin/integration-cleanup
else ifdef OPENSTACK_USER
	echo -e "\nRunning integration test cleanup script with credentials from environment variables..."
	bin/integration-cleanup
else
	echo -e "\nIntegration test cleanup script skipped (create a '.env.integration' file to run them)"
endif

test.new_integration_cleanup: clean ## Run the integration cleanup script.
ifneq ($(wildcard .env.integration),)
	echo -e "\nRunning integration test cleanup script with credentials from .env.integration file..."
	PYTHONPATH=$PYTHONPATH:$(pwd) honcho -e .env.integration run python3 cleanup_utils/integration_cleanup.py --dry_run
else ifdef OPENSTACK_USER
	echo -e "\nRunning integration test cleanup script with credentials from environment variables..."
	PYTHONPATH=$PYTHONPATH:$(pwd) python3 cleanup_utils/integration_cleanup.py --dry_run
else
	echo -e "\nIntegration test cleanup script skipped (create a '.env.integration' file to run them)"
endif

test.js: clean static_external ## Run JS tests.
	cd instance/tests/js && $(RUN_JS_TESTS)
	cd registration/tests/js && $(RUN_JS_TESTS)

test.instance_js_web: clean static_external ## Run instance-specific JS tests.
	cd instance/tests/js && jasmine --host 0.0.0.0

test.registration_js_web: clean static_external ## Run registration-specific JS tests.
	cd registration/tests/js && jasmine --host 0.0.0.0

test: clean test.quality test.unit test.migrations_missing test.js test.browser test.integration ## Run all tests.
	@echo "\nAll tests OK!\n"

test.one: clean
	$(HONCHO_MANAGE_TESTS) test $(RUN_ARGS)

# Files #######################################################################

static_external:
	$(MAKE) -C static/external
