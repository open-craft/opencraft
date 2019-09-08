Installation
------------

### Vagrant installation

For development, we recommend using [Vagrant](https://www.vagrantup.com/)
to automatically provision a development environment in a virtual machine. This
helps to keep your development environment isolated from the rest of your
system.

Vagrant uses [VirtualBox](https://www.virtualbox.org/) to create isolated
virtual machines with the developer environment set up. To provision and
configure the developer environment as needed Vagrant uses
[Ansible](https://www.ansible.com/).

You will need to install all these tools before you can set up your development
environment:

- [Vagrant Download](https://www.vagrantup.com/downloads.html)
- [VirtualBox Download](https://www.virtualbox.org/wiki/Downloads)

Once you have these tools installed, you will need to download the [Ansible
playbooks](https://github.com/open-craft/ansible-playbooks) used to build the
Vagrant instance.  If you haven't checked it out yet, you can clone it into the
`deploy/` subdirectory using this command at the root of the repository:

    git clone https://github.com/open-craft/ansible-playbooks deploy

If you already have a clone of that repo, you can also create a symlink `deploy`
pointing to your clone.

Create a new virtualenv to install the dependencies of the `ansible-playbooks`
repository – most notably Ansible:

    virtualenv ~/venvs/ansible    # Adjust the path, or use mkvirtualenv
                                  # if you have virtualenvwrapper installed.
    ~/venvs/ansible/bin/activate
    pip install -r deploy/requirements.txt

Now you can run

    vagrant up

This will provision a virtual machine running Ubuntu 16.04, set up local
Postgres, MySQL, MongoDB and Redis, and install the dependencies.

Once the virtual machine is up and running, you can ssh into it with this
command:

    vagrant ssh

To check if everything is set up properly you can run ``make test.unit`` inside
your new environment.

Vagrant will set up a VirtualBox share mapping your local development directory
to `/vagrant` inside the virtual machine. Any changes you make locally will be
reflected inside the virtual machine automatically.

Vagrant will map port 5000 inside the virtual machine to port 5000 on the host.
Once you have set everything up you will be able to access the development
server at http://localhost:5000/ using your web browser.

### Local installation (skip this if using Vagrant)

If you prefer not to use Vagrant, you can install OpenCraft Instance Manager manually.
Refer to the [Ansible playbooks](https://github.com/open-craft/ansible-opencraft) used
by Vagrant for an example. Instructions based on Ubuntu 16.04.

Install the system package dependencies & virtualenv:

    make install_system_dependencies
    pip3 install --user virtualenv

You might also need to install PostgreSQL, MySQL and MongoDB:

    make install_system_db_dependencies

Note that the tests expect to be able to access MySQL on localhost using the
default port, connecting as the root user without a password.

Create a virtualenv, source it, and install the python requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
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

To run the production server:

    make run

To change the number of concurrent gunicorn workers run by the production
server:

    make run WORKERS=2

Process description
-------------------

This runs three processes via Honcho, which reads `Procfile` or `Procfile.dev`
and loads the environment from the `.env` file:

* *web*: the main HTTP server (Django + Werkzeug debugger in dev, gunicorn in prod)
* *worker*: runs asynchronous jobs (Huey)

Important: the Werkzeug debugger started by the development server allows remote
execution of Python commands. It should *not* be run in production.

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
