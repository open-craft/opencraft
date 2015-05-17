OpenCraft
=========

Install
-------

Install the dependencies in a Python 3 virtual environment:

    $ sudo apt-get install `cat debian_packages.lst`
    $ mkvirtualenv -p /usr/bin/python3 opencraft
    $ pip install -r requirements.txt


Configure
---------

Customize the sample settings file:

    $ cp opencraft/local_settings.sample opencraft/local_settings.py
    $ gvim opencraft/local_settings.py


Run
---

To start the development environment server:

    $ ./manage.py migrate
    $ ./manage.py collectstatic --noinput
    $ ./manage.py runserver_plus

Then go to:

* User interface: [http://localhost:2000/](http://localhost:2000/)
* API: [http://localhost:2000/api/](http://localhost:2000/api/)
* Admin: [http://localhost:2000/admin/](http://localhost:2000/admin/)

Default configuration specific to the development environment is stored in `opencraft/dev.py`.


Production
----------

For the production environment, use the `prod` settings:

    $ ./manage.py print_settings --settings=prod

Debug
-----

To access the console, you can use `shell_plus`:

    $ ./manage.py shell_plus
