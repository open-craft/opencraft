clean:
	find -name '*.pyc' -delete
	find -name '*~' -delete
	find -name '__pycache__' -type d -delete

collectstatic:
	honcho run ./manage.py collectstatic --noinput

migrate:
	honcho run ./manage.py migrate

run: clean migrate collectstatic
	honcho start

rundev: clean migrate
	honcho start -f Procfile.dev

shell:
	honcho run ./manage.py shell_plus

test:
	prospector --profile opencraft
