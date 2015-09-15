# Config
WORKERS = 4
SHELL = /bin/bash
MANAGE := python ./manage.py
HONCHO_MANAGE := honcho run $(MANAGE)

.PHONY: install_system_dependencies
install_system_dependencies:
	sudo apt-get install -y `tr -d '\r' < debian_packages.lst`

.PHONY: install_virtualenvwrapper_py3
install_virtualenvwrapper_py3:
	pip3 install --user virtualenv && pip3 install --user virtualenvwrapper

# For `test_one` use the rest as arguments and turn them into do-nothing targets
ifeq (test_one,$(firstword $(MAKECMDGOALS)))
  RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
  $(eval $(RUN_ARGS):;@:)
endif

clean:
	find -name '*.pyc' -delete
	find -name '*~' -delete
	find -name '__pycache__' -type d -delete
	rm -rf .coverage build

collectstatic: clean
	$(HONCHO_MANAGE) collectstatic --noinput

migrate: clean
	$(HONCHO_MANAGE) migrate

migration_check: clean
	!(($(HONCHO_MANAGE) showmigrations | grep '\[ \]') && printf "\n\033[0;31mERROR: Pending migrations found\033[0m\n\n")

run: clean migration_check collectstatic
	honcho start --concurrency "worker=$(WORKERS)"

rundev: clean migration_check
	honcho start -f Procfile.dev

shell:
	$(HONCHO_MANAGE) shell_plus

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

test: clean test_prospector test_unit test_integration
	@echo -e "\nAll tests OK!\n"

test_one: clean
	honcho -e .env.test run ./manage.py test $(RUN_ARGS)

upgrade_dependencies:
	pip freeze --local | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U
