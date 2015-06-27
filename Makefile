clean:
	find -name '*.pyc' -delete
	find -name '*~' -delete
	find -name '__pycache__' -type d -delete

test:
	prospector --uses django
	honcho run ./manage.py test
