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

# Config ######################################################################

# Any configuration variable can be overridden with `VARIABLE = VALUE` in a git-ignored `private.mk` file.

.DEFAULT_GOAL := help
HELP_SPACING ?= 30
COVERAGE_THRESHOLD ?= 90
WORKERS ?= 3
WORKERS_LOW_PRIORITY ?= 3
SHELL ?= /bin/bash
HONCHO_MANAGE := honcho run python3 manage.py
HONCHO_MANAGE_TESTS := honcho -e .env.test run python3 manage.py
HONCHO_COVERAGE_TEST := honcho -e .env.test run coverage run --branch --parallel-mode ./manage.py test --noinput -v2
HONCHO_COVERAGE_INTEGRATION := honcho -e .env.integration run coverage run --branch --parallel-mode ./manage.py test --noinput -v2
COVERAGE := coverage run --branch --parallel-mode ./manage.py test --noinput -v2

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

clean: cov.clean ## Remove all temporary files.
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
	if [ -z $$CI ] ; then \
		echo "Installing Firefox because we're not in a CI."; \
		sudo apt-get install -y libgtk3.0-cil-dev libasound2 libasound2 libdbus-glib-1-2 libdbus-1-3 --no-install-recommends; \
		sudo curl -sL -o /tmp/firefox.deb 'https://s3.amazonaws.com/circle-downloads/firefox-mozilla-build_47.0.1-0ubuntu1_amd64.deb'; \
		echo 'ef016febe5ec4eaf7d455a34579834bcde7703cb0818c80044f4d148df8473bb  /tmp/firefox.deb' | sha256sum -c; \
		sudo dpkg -i /tmp/firefox.deb || sudo apt-get -f install; \
		sudo rm -rf /tmp/firefox.deb; \
	else \
		echo "Not installing Firefox because this is a CI."; \
	fi

install_js_dependencies: ## Install dependencies for JS code.
	curl -sL https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
	echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
	sudo apt-get update
	sudo apt-get install -y yarn
	yarn install

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
	$(HONCHO_COVERAGE_TEST)

test.migrations_missing: clean ## Check if migrations are missing.
	@$(HONCHO_MANAGE_TESTS) makemigrations --dry-run --check

test.browser: clean static_external ## Run browser-specific tests.
	@echo -e "\nRunning browser tests..."
	xvfb-run --auto-servernum $(HONCHO_COVERAGE_TEST) --pattern=browser_*.py
	
test.integration: clean ## Run integration tests.
ifneq ($(wildcard .env.integration),)
	echo -e "\nRunning integration tests with credentials from .env.integration file..."
	$(HONCHO_COVERAGE_INTEGRATION) --pattern=integration_*.py
else ifdef OPENSTACK_USER
	echo -e "\nRunning integration tests with credentials from environment variables..."
	$(COVERAGE) --pattern=integration_*.py
else
	echo -e "\nIntegration tests skipped (create a '.env.integration' file to run them)"
endif

test.integration_cleanup: clean ## Run the integration cleanup script.
ifneq ($(wildcard .env.integration),)
	echo -e "\nRunning integration test cleanup script with credentials from .env.integration file..."
	PYTHONPATH=$(PYTHONPATH):$(pwd) honcho -e .env.integration run python3 cleanup_utils/integration_cleanup.py
else ifdef OPENSTACK_USER
	echo -e "\nRunning integration test cleanup script with credentials from environment variables..."
	PYTHONPATH=$(PYTHONPATH):$(pwd) python3 cleanup_utils/integration_cleanup.py
else
	echo -e "\nIntegration test cleanup script skipped (create a '.env.integration' file to run them)"
endif

test.js: clean static_external ## Run JS tests.
ifeq ($(CIRCLECI),true)
	@./node_modules/.bin/karma start --single-run
else
	@xvfb-run ./node_modules/.bin/karma start --single-run
endif
	@if [ -e coverage/text/coverage.txt ]; then cat coverage/text/coverage.txt; fi

test: clean test.quality test.unit test.migrations_missing test.js test.browser test.integration cov.combine ## Run all tests.
	@echo "\nAll tests OK!\n"

test.one: clean
	$(HONCHO_MANAGE_TESTS) test $(RUN_ARGS)

# Files #######################################################################

static_external:
	$(MAKE) -C static/external

cov.html:
	coverage html
	@echo "\nCoverage HTML report at file://`pwd`/build/coverage/index.html\n"
	@coverage report --fail-under $(COVERAGE_THRESHOLD) || (echo "\nERROR: Coverage is below $(COVERAGE_THRESHOLD)%\n" && exit 2)

cov.combine:
	coverage combine

cov.clean:
	coverage erase
