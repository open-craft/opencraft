OpenCraft
=========

Dependencies: Python 3.x

Install
-------

Run the following commands::

    $ sudo apt-get install `cat debian_packages.lst`
    $ mkvirtualenv -p /usr/bin/python3 opencraft
    $ pip install -r requirements.txt

Configure
---------

To configure::

    $ cp opencraft/local_settings.sample opencraft/local_settings.py
    $ gvim opencraft/local_settings.py

Run
---

In the development environment::

    $ ./manage.py migrate
    $ ./manage.py collectstatic --noinput
    $ ./manage.py runserver_plus

For the production environment, use the `prod` settings::

    $ ./manage.py runserver_plus --settings=prod

To access the console, you can use `shell_plus`::

    $ ./manage.py shell_plus
