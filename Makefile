# Config
WORKERS = 4
SHELL = /bin/bash

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
	honcho run ./manage.py collectstatic --noinput

migrate: clean
	honcho run ./manage.py migrate

migration_check: clean
	!((honcho run ./manage.py showmigrations | grep '\[ \]') && printf "\n\033[0;31mERROR: Pending migrations found\033[0m\n\n")

run: clean migration_check collectstatic
	honcho start --concurrency "worker=$(WORKERS)"

rundev: clean migration_check
	honcho start -f Procfile.dev

shell:
	honcho run ./manage.py shell_plus

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

test_js: clean
	cd instance/tests/js && jasmine-ci --logs --browser firefox

test_js_web: clean
	cd instance/tests/js && jasmine

test: clean test_prospector test_unit test_js test_integration
	@echo -e "\nAll tests OK!\n"

test_one: clean
	honcho -e .env.test run ./manage.py test $(RUN_ARGS)

upgrade_dependencies:
	pip freeze --local | grep -v '^\-e' | cut -d = -f 1  | xargs -n1 pip install -U
