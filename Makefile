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
HONCHO_MANAGE := honcho run python3 manage.py 


# Parameters ##################################################################

# For `test_one` use the rest as arguments and turn them into do-nothing targets
ifeq (test_one,$(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif


# Commands ####################################################################

.PHONY: all
all:
	rundev

.PHONY: apt_get_update
apt_get_update:
	sudo apt-get update

.PHONY: clean
clean:
	find -name '*.pyc' -delete
	find -name '*~' -delete
	find -name '__pycache__' -type d -delete
	rm -rf .coverage build
	find static/external -type f -not -name 'Makefile' -not -name '.gitignore' -delete

.PHONY: install_system_db_dependencies
install_system_db_dependencies: apt_get_update
	sudo apt-get install -y `tr -d '\r' < debian_db_packages.lst`

.PHONY: install_system_dependencies
install_system_dependencies: apt_get_update
	sudo apt-get install -y `tr -d '\r' < debian_packages.lst`

.PHONY: install_virtualenv_system
install_virtualenv_system:
	sudo pip3 install virtualenv virtualenvwrapper

.PHONY: collectstatic
collectstatic: clean static_external
	honcho run ./manage.py collectstatic --noinput

.PHONY: migrate
migrate: clean
	$(HONCHO_MANAGE) migrate

.PHONY: migration_check
migration_check: clean
	!(($(HONCHO_MANAGE) showmigrations | grep '\[ \]') && printf "\n\033[0;31mERROR: Pending migrations found\033[0m\n\n")

.PHONY: migration_autogen
migration_autogen: clean
	$(HONCHO_MANAGE) makemigrations

.PHONY: run
run: clean migration_check collectstatic
	honcho start --concurrency "worker=$(WORKERS)"

.PHONY: rundev
rundev: clean migration_check static_external
	honcho start -f Procfile.dev

.PHONY: shell
shell:
	$(HONCHO_MANAGE) shell_plus

.PHONY: upgrade_dependencies
upgrade_dependencies:
	pip freeze --local | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U

# Tests #######################################################################

.PHONY: test_prospector
test_prospector: clean
	prospector --profile opencraft

.PHONY: test_unit
test_unit: clean
	honcho -e .env.test run coverage run --source='.' --omit='*/tests/*' ./manage.py test --noinput
	coverage html
	@echo -e "\nCoverage HTML report at file://`pwd`/build/coverage/index.html\n"
	@coverage report --fail-under 94 || (echo "\nERROR: Coverage is below 95%\n" && exit 2)

.PHONY: test_integration
test_integration: clean
	@if [ -a .env.integration ] ; then \
		echo -e "\nRunning integration tests..." ; \
		honcho -e .env.integration run ./manage.py test --pattern=integration_*.py --noinput ; \
	else \
		echo -e "\nIntegration tests skipped (create a '.env.integration' file to run them)" ; \
	fi

.PHONY: test_js
test_js: clean static_external
	cd instance/tests/js && jasmine-ci --logs --browser firefox

.PHONY: test_js_web
test_js_web: clean static_external
	cd instance/tests/js && jasmine --host 0.0.0.0

.PHONY: test
test: clean test_prospector test_unit test_js test_integration
	@echo -e "\nAll tests OK!\n"

.PHONY: test_one
test_one: clean
	honcho -e .env.test run ./manage.py test $(RUN_ARGS)


# Files #######################################################################

.PHONY: static_external
static_external:
	$(MAKE) -C static/external
