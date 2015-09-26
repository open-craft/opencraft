OpenCraft
=========

Install
-------

### Vagrant install

You can use [vagrant][] to set up a virtual machine for local development and
testing. This is useful to keep your development environment isolated from the
rest of your system.

First, install [virtualbox][] and [vagrant][]. Then run:

    vagrant up

This will provision a virtual machine running Ubuntu 14.04, set up local
postgres and redis, install the dependencies and run the tests.

Once the virtual machine is up and running, you can ssh into it with this
command:

    vagrant ssh

Vagrant will set up a virtualbox share mapping your local development directory
to `/vagrant` inside the virtual machine. Any changes you make locally will be
reflected inside the virtual machine automatically.

Vagrant will map port 5000 inside the virtual machine to port 5000 on the host,
so you can access the development server using your web browser.


### Local install

If you prefer not to install vagrant, you can install OpenCraft manually.
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
$ workon opencraft
$ pip install -r requirements.txt
```


Configure
---------

Honcho will set up environment variables defined in the `.env` file at the root
of your repository. If you are using vagrant for development, a basic `.env`
file will already have been created for you, but you will need to add
credentials for third-party services manually in order to run the development
server or the integration tests.

The environment variables in `.env` customize the settings from
`opencraft/settings.py` which are loaded via `env()`.


Migrations
----------

To run database migrations:

```
$ make migrate
```

The startup commands such as `make run` and `make rundev` check for pending migrations, and will 
exit before starting the server if any are found. You can also check for pending migrations manually with:

```
$ make migration_check
```


Run
---

To run the development server:

```
$ make rundev
```

Then go to:

* User interface: [http://localhost:5000/](http://localhost:5000/)
* API: [http://localhost:5000/api/](http://localhost:5000/api/)
* Admin: [http://localhost:5000/admin/](http://localhost:5000/admin/)

To run the production server:

```
$ make run
```

To change the number of concurrent workers ran by the production server:

```
$ make run WORKERS=2
```



Process description
-------------------

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


Running the tests
-----------------

First, the current user can access postgresql and create databases, for the test database. Run:

```
$ sudo -u postgres createuser -d <currentunixuser>`
```

Where `<currentunixuser>` is replaced with the name of whatever user the app runs under. Then run 
the whole test suite (pylint, pyflakes, pep8, unit tests, etc.) with:

```
$ make test
```

To run a single test, use `make test_one`:

```
$ make test_one instance.tests.models.test_server
```

You can also run prospector and the unit tests independently:

```
$ make test_prospector
$ make test_unit
$ make test_integration
```

Note that the integration tests aren't run by default, as they require a working
OpenStack cluster configured. To run them, create a `.env.integration` file -
your development environment is likely a good starting point:

```
$ ln -s .env .env.integration
```


Debug
-----

To access the console, you can use `shell_plus`:

```
$ make shell
```


Manage.py
---------

You can also access the Django `manage.py` command directly, using honcho to load the environment:

```
$ honcho run ./manage.py config
```


[virtualbox]: https://www.virtualbox.org/
[vagrant]:    https://www.vagrantup.com/
