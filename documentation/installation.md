# Installation

## Vagrant installation

Vagrant toolchain is no longer supported,
Docker is the recommended [development setup](development/docker.md).

### Local installation (skip this if using docker)

If you prefer not to use docker, you can install OpenCraft Instance Manager manually.
Refer to the [Ansible playbooks](https://github.com/open-craft/ansible-playbooks).
Ocim requires Python 3.6 or a newer version. The instructions here are based on
Ubuntu 16.04. Since Ubuntu 16.04 ships with Python 3.5, we will use `pyenv` to
install a newer, supported version on it. This is not required when a supported
version of Python is available. All the `pyenv` commands can be then ignored
and the built-in `venv` module can be used to create a virtualenv environment.

Install [pyenv](https://github.com/pyenv/pyenv) by following the [pyenv documentation](https://github.com/pyenv/pyenv#installation).
Also install [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv#installation) by following its [documentation](https://github.com/pyenv/pyenv-virtualenv#installation).

Install a supported version of Python and create a virtualenv environment. We will be using Python 3.6.10 as an example.

    pyenv install 3.6.10

Install the system package dependencies:

    make install_system_dependencies

You might also need to install PostgreSQL, MySQL and MongoDB:

    make install_system_db_dependencies

Note that the tests expect to be able to access MySQL on localhost using the
default port, connecting as the root user without a password.

Create a virtualenv, activate it, and install the python requirements:

    pyenv virtualenv 3.6.10 opencraft
    pyenv activate opencraft
    pip install -r requirements.txt

You will need to create a database user to run the tests:

    sudo -u postgres createuser -d <currentunixuser>

Where `<currentunixuser>` is the name of whatever user the app runs under.

When you have finished setting everything up, run the unit tests to make sure
everything is working correctly:

    make test.unit

Migrations
----------

To run database migrations:

    make migrate

The startup commands such as `make run` and `make run.dev` check for pending
migrations, and will exit before starting the server if any are found. You can
also check for pending migrations manually with:

    make migrations.check

Run
---

To run the development server:

    make run.dev

Then go to:

* User interface: [http://localhost:5000/](http://localhost:5000/)
* API: [http://localhost:5000/api/](http://localhost:5000/api/)
* Admin: [http://localhost:5000/admin/](http://localhost:5000/admin/)

You will also want to start up the [Frontend](#ocim-frontend).

To run the production server:

    make run

To change the number of concurrent gunicorn workers run by the production
server:

    make run WORKERS=2

Process description
-------------------

This runs multiple processes via Honcho, which reads `Procfile` or `Procfile.dev`
and loads the environment from the `.env` file:

* *web*: runs an ASGI server supporting HTTP and Websockets in dev and a WSGI HTTP server using gunicorn in productino.
* *websocket*: runs an ASGI websocket server in production.
* *worker\**: runs asynchronous jobs (Huey).
* *periodic*: runs periodic, asynchronous jobs in production (Huey).

Static assets collection
------------------------

The web server started in the development environment also doesn't require
collectstatic to run after each change.

The production environment automatically runs collectstatic on startup, but you
can also run it manually:

    make static

Running the tests
-----------------

To run the whole test suite (pylint, pyflakes, pep8, unit tests, etc.):

    make test

To run a single test, use `make test.one`:

    make test.one instance.tests.models.test_server

You can also run Prospector, the unit tests, JS tests and integration tests
independently:

    make test.quality
    make test.unit
    make test.js
    make test.integration

JS tests can be run in your browser for debugging (run `make test.instance_js_web`
or `make test.registration_js_web` and then go to http://localhost:8888/), or in a
CI manner via selenium and `jasmine-ci` (run `make test.js`).

Note that the integration tests aren't run by default, as they require a working
OpenStack cluster configured. To run them, create a `.env.integration` file -
your development environment is likely a good starting point:

    cp .env .env.integration

There is also a cleanup routine intended for use by CI services to check for
and clean up any dangling OpenStack VMs and MySQL databases past a certain age
threshold. While it isn't necessary in the usual case, old integration tests
that were killed without cleanup and old MySQL databases that are older than
three days can be cleaned up by running the make target:

    make test.integration_cleanup

Debug
-----

To access the console, you can use `shell_plus`:

    make shell

## OCIM Frontend

The frontend of OCIM is a single-page app using React and Redux.
All the code can be found inside `frontend` directory.
All reusable UI components description been described in the `/demo` route in dev environment.

### Provisioning

Check the Frontend README all the instructions are given there.
