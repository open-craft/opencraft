# Defaults
WORKERS = 4

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

run: clean migrate collectstatic
	honcho start --concurrency "worker=$(WORKERS)"

rundev: clean migrate
	honcho start -f Procfile.dev

shell:
	honcho run ./manage.py shell_plus

test_prospector: clean
	prospector --profile opencraft

test_unit: clean
	honcho -e .env.test run coverage run --source='.' --omit='*/tests/*' ./manage.py test
	coverage html
	@echo "\nCoverage HTML report at file://`pwd`/build/coverage/index.html\n"
	@coverage report --fail-under 94 || (echo "\nERROR: Coverage is below 95%\n" && exit 2)

test: clean test_prospector test_unit

test_one: clean
	honcho -e .env.test run ./manage.py test $(RUN_ARGS)
