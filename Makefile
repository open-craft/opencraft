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
	honcho start

rundev: clean migrate
	honcho start -f Procfile.dev

shell: clean
	honcho run ./manage.py shell_plus

test: clean
	prospector --profile opencraft
	honcho -e .env.test run coverage run --source='.' ./manage.py test
	coverage html
	@echo "\nCoverage HTML report at file://`pwd`/build/coverage/index.html\n"
	@coverage report --fail-under 90 || (echo "\nERROR: Coverage is below 90%\n" && exit 2)
