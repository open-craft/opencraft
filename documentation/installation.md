Installation
------------

### Vagrant installation

For development, we recommend using [Vagrant](https://www.vagrantup.com/)
to automatically provision a development environment in a virtual machine. This
helps to keep your development environment isolated from the rest of your
system.

Vagrant uses [VirtualBox](https://www.virtualbox.org/) to create isolated
virtual machines with the developer environment set up. To provision and
configure the developer environment as needed, Vagrant uses
[Ansible](https://www.ansible.com/).

First, make sure that Intel VT-x/AMD-v virtualization is enabled in your BIOS / UEFI
firmware. Then, you will need to install all these tools before you can set up your
development environment:

- [Vagrant Download](https://www.vagrantup.com/downloads.html)
- [VirtualBox Download](https://www.virtualbox.org/wiki/Downloads)

Install the plugin vagrant-vbguest:

    vagrant plugin install vagrant-vbguest

Once you have these tools installed, download the [Ocim repository]
(https://github.com/open-craft/opencraft) if you have not already done it.

    git clone https://github.com/open-craft/opencraft ocim
    cd ocim

Also download the [Ansible playbooks](https://github.com/open-craft/ansible-playbooks)
used to build the Vagrant instance into the `deploy/` subdirectory:

    git clone https://github.com/open-craft/ansible-playbooks deploy

If you already have a clone of that repository, create a symlink `deploy`
pointing to it instead:

    ln -s <cloned_repo_path> deploy

Create a new virtualenv to install the dependencies of the `ansible-playbooks`
repository – most notably Ansible:

    virtualenv ~/venvs/ansible    # Adjust the path, or use mkvirtualenv
                                  # if you have virtualenvwrapper installed.
    . ~/venvs/ansible/bin/activate
    pip install -r deploy/requirements.txt

Now you can run:

    vagrant up

This will provision a virtual machine running Ubuntu 16.04, set up local
Postgres, MySQL, MongoDB and Redis, and install the dependencies.

Once the virtual machine is up and running, you can ssh into it with this
command:

    vagrant ssh

Inside the virtual machine, set HUEY_ALWAYS_EAGER to false in
/home/vagrant/opencraft/.env. Also, create a superuser account which will
be used to log in to Ocim:

    make manage createsuperuser

To check if everything is set up properly, you can run ``make test.unit`` inside
your new environment.

Vagrant will set up a VirtualBox share mapping your local development directory
to `/vagrant` inside the virtual machine. Any changes you make locally will be
reflected inside the virtual machine automatically.

Vagrant will map port 5000 inside the virtual machine to port 5000 on the host.
Once you have set everything up, you will be able to access the home webpage of
the development server at http://localhost:5000/ using your web browser. Log in
with the previously created superuser account credentials and you will then be
redirected to the Ocim webpage which lists the Open edX instances.

### Local installation (skip this if using Vagrant)

If you prefer not to use Vagrant, you can install OpenCraft Instance Manager manually.
Refer to the [Ansible playbooks](https://github.com/open-craft/ansible-playbooks) used
by Vagrant for an example. Ocim requires Python 3.6 or a newer version. The instructions
here are based on Ubuntu 16.04. Since Ubuntu 16.04 ships with Python 3.5, we will use `pyenv`
to install a newer, supported version on it. This is not required when a supported version of
Python is available. All the `pyenv` commands can be then ignored and the built-in `venv` module
can be used to create a virtualenv environment.

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

The frontend of OCIM is a single-page app using the React and Redux. All the code can be found inside `frontend` directory.

### Provisioning

- Install the API client:

```bash
./scripts/build-api-client.sh
```

- Install requirements:

```bash
npm install
```

- Run frontend:

```bash
npm start
```

- Updating the API Client:

```bash
cd ./frontend # go to frontend directory
npm run update-api-client
```

- Building the API Client:

```bash
cd ./frontend # go to frontend directory
npm run build-api-client
```

- Deployment:

We use the screen for running the OCIM in production and staging. For this ssh into staging or production servers

```bash
# go to screen session where the OCIM running(most probably it will be with
# suffix .stage or .console) and go to bash window
# fetch the latest changes
git fetch


# go to screen window where the OCIM running(probably the first window)
# based on the environment(Staging or Production), you might have to stop
# the NewRelic Monitoring and then stop the OCIM running service
make run


# Go to the shell window and restart the shell by exiting and running it again
make shell
```

### Running with Vagrant

While it is possible to run this frontend server within Vagrant during
development, for performance reasons it's better to run it separately
outside of Vagrant instead.

### Frontend Architecture/Stack

We use React, TypeScript, Bootstrap, and SCSS for the frontend.

For global state shared among different parts of the application, we use Redux.
So things like the user's login/logout status, the user's details etc. should
be kept in the Redux state and modified using actions.

For all other state, such as data required just for a particular
widget/component/page, we just use "normal" React props/state; this is because
Redux imposes a lot of boilerplate code overhead and offers little value if the
state is not shared among diverse parts of the application.

However, just because we use React and, when necessary, Redux, this doesn't mean
all the code has to be inside React components or the Redux store; "regular"
JavaScript code launched from main.tsx that for example talks to the Redux
store is always an option.

### React Component Guidelines

When coding React components, please keep the following in mind:

- All components should subclass [`React.PureComponent`](https://reactjs.org/docs/react-api.html#reactpurecomponent).
- All component props and redux state variables that are complex objects should be immutable (enforced via TypeScript by declaring them as `ReadOnlyArray<T>`, `ReadOnlySet<T>`, and `ReadOnly<T>`, mutated using [`immutability-helper`](https://github.com/kolodny/immutability-helper) or plain ES6).
- Write sensible tests, including unit tests, [snapshot tests](https://jestjs.io/docs/en/snapshot-testing), and/or end-to-end tests.
  - When reviewing changes to snapshot tests, carefully review the HTML diff to ensure the changes are expected.
  - Test files should be located alongside the component they test (so `Card.tsx` is tested in `Card.spec.tsx`)
  - Never import jest/test related code in `.ts` files that are part of the application (only in `.spec.tsx` files); this avoids adding several megabytes of test code to the app bundle.
  - When in doubt, end-to-end tests and Enzyme behavior tests are preferred. Snapshot tests are still useful, but not as important as an end to end test or even a regular React component test that simulates user interaction with the component and then make assertions about the result.
- Prefer to split big components up into smaller components that get composed together.
- Use the [Container Pattern](https://medium.freecodecamp.org/react-superpowers-container-pattern-20d664bdae65)
  - Don't write a `FoobarComponent` that loads `Foobar` data from the REST API then renders it; instead write a `FoobarComponent` that accepts `Foobar` data as a prop (so its props are never `undefined`), and then write a `FoobarContainerComponent` which loads the `Foobar` data from the REST API and then once it's loaded renders a `<FoobarComponent data={foobarData}/>`. This lets us test the presentation/UX separately from the API/backend, provides better separation of concerns, and reduces the need to write code that checks if the prop has data or not when rendering.
- Make sure the component is internationalized (see below) and accessible.
