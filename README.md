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


Ansible worker queue
--------------------

Install ansible and the configuration repository:

   $ cd .. # Go outside of the current repository
   $ git clone https://github.com/edx/configuration.git
   $ cd configuration
   $ mkvirtualenv edx-configuration
   $ pip install -r requirements.txt

Then configure the _Ansible worker queue` section in `local_settings.py`. You will need access to
an OpenStack API and a domain hosted on Gandi.

To run the jobs queue:

   $ ./manage.py run_huey


Debug
-----

To access the console, you can use `shell_plus`:

    $ ./manage.py shell_plus
