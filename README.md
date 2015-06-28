OpenCraft
=========

Install
-------

Instructions based on Ubuntu 14.04.

Install the system package dependencies & virtualenv:

```
$ sudo apt-get install `cat debian_packages.lst`
$ pip3 install --user virtualenv && pip3 install --user virtualenvwrapper
```

Ensure you load virtualenv with Python 3 in `~/.bashrc`:

```
export PATH="$PATH:$HOME/.local/bin" VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source $HOME/.local/bin/virtualenvwrapper.sh
```

Then reload `~/.bashrc`, create the virtual env and install the Python requirements:

```
$ . ~/.bashrc
$ mkvirtualenv -p /usr/bin/python3 opencraft
$ pip install -r requirements.txt
```


Configure
---------

Create an `.env` file at the root of the repository or set environment variables, customizing the
settings from `opencraft/settings.py` which are loaded via `env()`.


Run
---

To run the development server:

```
$ make rundev
```

Then go to:

* User interface: [http://localhost:5000/](http://localhost:2000/)
* API: [http://localhost:5000/api/](http://localhost:2000/api/)
* Admin: [http://localhost:5000/admin/](http://localhost:2000/admin/)

To run the production server:

```
$ make run
```


Processus description
---------------------

This runs three processus via honcho, which reads `Procfile` or `Procfile.dev` and loads the
environment from the `.env` file:

* *web*: the main HTTP server (Django - Werkzeug debugger in dev, gunicorn in prod)
* *websocket*: the websocket server (Tornado)
* *worker*: runs asynchronous jobs (Huey)

Important: the Werkzeug debugger started by the development server allows remote execution
of Python commands. It should *not* be run in production.


Static assets collection
------------------------

The Web server started in the development environment also doesn't require to run collectstatic
after each change.

The production environment automatically runs collectstatic on startup, but you can also run it
manually:

```
$ make collectstatic
```


Migrations
----------

Similarly, migrations are run automatically on startup - for both the development and production
environments. To run it manually:

```
$ make migrate
```


Running the tests
-----------------

First, ensure that the postgresql user can create databases, to be able to create the test database. 
Then run the whole test suite (pylint, pyflakes, pep8, unit tests, etc.) with:

```
$ make test
```


Debug
-----

To access the console, you can use `shell_plus`:

```
$ make shell

Python 3.4.3 (default, Mar 26 2015, 22:03:40)
Type "copyright", "credits" or "license" for more information.

IPython 3.1.0 -- An enhanced Interactive Python.
?         -> Introduction and overview of IPython's features.
%quickref -> Quick reference.
help      -> Python's own help system.
object?   -> Details about 'object', use 'object??' for extra details.

In [1]: from instance.tasks import provision_sandbox_instance

In [2]: result = provision_sandbox_instance(
    sub_domain='badges.sandbox',
    name='Badges',
    s3_access_key='XXX',
    s3_secret_access_key='XXX',
    s3_bucket_name='sandbox-edxapp-storage',
)
```


Manage.py
---------

You can also access the Django `manage.py` command directly, using honcho to load the environment:

```
$ honcho run ./manage.py config
```
