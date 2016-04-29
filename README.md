OpenCraft Instance Manager
==========================

[![Circle CI](https://img.shields.io/circleci/project/open-craft/opencraft/master.svg)](https://circleci.com/gh/open-craft/opencraft/tree/master) [![Requirements Status](https://requires.io/github/open-craft/opencraft/requirements.svg?branch=master)](https://requires.io/github/open-craft/opencraft/requirements/?branch=master)

The OpenCraft Instance Manager is a Django application to deploy and manage
[Open edX](https://open.edx.org/) sandboxes on
[OpenStack](https://www.openstack.org/) virtual machines. It is primarily
intended for testing new features, and can deploy sandboxes automatically from
GitHub pull requests.


Install
-------

### Vagrant install

For development, we recommend using [Vagrant](https://www.vagrantup.com/)
to automatically provision a development environment in a virtual machine. This
helps to keep your development environment isolated from the rest of your
system.

First, install [VirtualBox](https://www.virtualbox.org/wiki/Downloads) and
[Vagrant](https://www.vagrantup.com/downloads.html). Then run:

    vagrant up

This will provision a virtual machine running Ubuntu 14.04, set up local
Postgres, MySQL, MongoDB and Redis, install the dependencies and run the tests.

Once the virtual machine is up and running, you can ssh into it with this
command:

    vagrant ssh

Vagrant will set up a VirtualBox share mapping your local development directory
to `/vagrant` inside the virtual machine. Any changes you make locally will be
reflected inside the virtual machine automatically.

Vagrant will map port 5000 inside the virtual machine to port 5000 on the host,
so you can access the development server at http://localhost:5000/ using your
web browser.

### Local install (skip this step if using Vagrant)

If you prefer not to use Vagrant, you can install OpenCraft manually. Refer to
the [bootstrap](bin/bootstrap) script used by Vagrant for an example.
Instructions based on Ubuntu 14.04.

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

    make test_unit


Configure
---------

Honcho will set up environment variables defined in the `.env` file at the root
of your repository. If you are using vagrant for development, a basic `.env`
file will already have been created for you, but you will need to add
credentials for third-party services manually in order to run the development
server or the integration tests.

The environment variables in `.env` customize the settings from
`opencraft/settings.py` which are loaded via `env()`. For more information about
each setting, see the [list of settings](#application-settings) below, and
[`opencraft/settings.py`](opencraft/settings.py). As a minimum, you will need to
add credentials for OpenStack, Gandi and GitHub. You can use this example `.env`
file as a starting point:

```sh
SECRET_KEY='...'
DATABASE_URL='postgres://localhost/opencraft'
OPENSTACK_USER='username'
OPENSTACK_PASSWORD='password'
OPENSTACK_TENANT='tenant-name'
OPENSTACK_AUTH_URL='https://auth.cloud.ovh.net/v2.0'
OPENSTACK_REGION='BHS1'
OPENSTACK_SANDBOX_SSH_KEYNAME='keypair-name'
INSTANCES_BASE_DOMAIN='example.com'
GANDI_ZONE_ID='123456789'
GANDI_API_KEY='api-key'
GITHUB_ACCESS_TOKEN='github-token'
WATCH_ORGANIZATION='github-org'
```

### A note on SSH keys

The instance manager uses [Ansible](https://www.ansible.com/) to provision
openedx sandboxes. Ansible uses SSH to run commands on remote servers, so you
will need to configure the instance manager with an SSH key pair to use for this
purpose.

First, **as the user that the instance manager runs as (e.g. `vagrant`)**, run:

    ssh-keygen -t rsa -b 4096

This will create an ssh key pair for that user, saving it at `~/.ssh/id_rsa` and
`~/.ssh/id_rsa.pub` by default. Next, we need to upload the public key to
OpenStack. Make sure the nova command line client is installed:

    pip install python-novaclient

[Configure the client with your OpenStack credentials](http://docs.openstack.org/cli-reference/common/cli_set_environment_variables_using_openstack_rc.html),
then run:

    nova keypair-add --pub_key ~/.ssh/id_rsa.pub KEY_NAME

where `KEY_NAME` is the name used to identify this key pair in OpenStack. The
`OPENSTACK_SANDBOX_SSH_KEYNAME` setting in your `.env` file should be set to
this name.

### OpenStack images

Open edX is currently designed to run on Ubuntu 12.04. Your OpenStack host may
already have an image available for this version of Ubuntu, but for maximum
compatibility we recommend the
[official Ubuntu cloud image](https://cloud-images.ubuntu.com/precise/current/).
To add this image to OpenStack, install glance:

    pip install python-glanceclient

Then, fetch the image and add it to OpenStack:

    wget https://cloud-images.ubuntu.com/precise/current/precise-server-cloudimg-amd64-disk1.img
    glance image-create \
      --disk-format=qcow2 \
      --container-format=bare \
      --file precise-server-cloudimg-amd64-disk1.img \
      --name IMAGE_NAME \
      --progress

where `IMAGE_NAME` is the name used to identify the image in OpenStack. The
`OPENSTACK_SANDBOX_BASE_IMAGE` setting in your `.env` file should match this
name:

    OPENSTACK_SANDBOX_BASE_IMAGE='{"name": "IMAGE_NAME"}'

### OpenStack flavors

OpenStack instances come in various
[flavors](http://docs.openstack.org/openstack-ops/content/flavors.html),
roughly equivalent to EC2 instance sizes. You must specify a flavor to use for
sandboxes. To see a list of available flavors, run:

    nova flavor-list

Set the `OPENSTACK_SANDBOX_FLAVOR` setting in your `.env` file to your chosen
flavor:

    OPENSTACK_SANDBOX_FLAVOR='{"name": "m1.medium"}'

### Application settings

* `DEBUG` Turn on debug mode. Use in development only (default: False)
* `SECRET_KEY` Set this to something unique and keep it secret (required)
* `DATABASE_URL` Your database, e.g. `postgres://localhost/opencraft` (required)
* `REDIS_URL` (default: `redis://localhost:6379/`)
* `HUEY_ALWAYS_EAGER` Set to True to run huey tasks synchronously, in the web
  process. Use in development only (default: False)
* `LOGGING_ROTATE_MAX_KBYTES`: The max size of each log file (in KB, default: 10MB)
* `LOGGING_ROTATE_MAX_FILES`: The max number of log files to keep (default: 60)

### OpenStack credentials

* `OPENSTACK_USER` Your openstack username (required)
* `OPENSTACK_PASSWORD` Your openstack password (required)
* `OPENSTACK_TENANT` Your openstack tenant name (required)
* `OPENSTACK_AUTH_URL` Your openstack auth url (required)
* `OPENSTACK_REGION` The openstack region to deploy sandboxes in (required)

### DNS settings

* `INSTANCES_BASE_DOMAIN` Instances are created as subdomains of this domain,
  e.g. `example.com` (required)
* `GANDI_ZONE_ID` The instance manager uses
  [gandi.net](https://www.gandi.net/domain/zones) to set up DNS for sandboxes.
  This should be set to the zone attached to the domain set at
  `INSTANCES_BASE_DOMAIN` (required). To find it:
  1. Login on your domain at [Gandi](https://www.gandi.net/)
  2. Go to -> Services > Domains > [yourdomain].com > Zone files > Edit the zone
  3. Get id from URL, eg. 00000000 for
     https://www.gandi.net/admin/domain/zone/00000000/2/edit?fromDomain=3889
     Needs to be an integer, not a string.
* `GANDI_API_KEY` Your Gandi API key (required)

### GitHub settings

* `GITHUB_ACCESS_TOKEN` Your GirHub access token (required). Get it from
  https://github.com/settings/tokens
* `WATCH_ORGANIZATION` The organization to watch (required). The instance
  manager will automatically set up sandboxes for pull requests made by members
  of this organization.
* `WATCH_FORK` Sandboxes are created for pull requests made against this fork
  (default: `edx/edx-platform`)

### Sandbox settings

* `OPENSTACK_SANDBOX_FLAVOR` A json string specifying the instance flavor to use
  (default: `{"ram": 4096, "disk": 40}`)
* `OPENSTACK_SANDBOX_BASE_IMAGE` A json string specifying the base image to use
  (default: `{"name": "Ubuntu 12.04"}`)
* `OPENSTACK_SANDBOX_SSH_KEYNAME` The name of the default ssh key pair used to
  connect to sandbox instances (default: `opencraft`). This key pair should be
  [registered with OpenStack](http://docs.openstack.org/user-guide/cli_nova_configure_access_security_for_instances.html)
  first, and should be the default ssh key for the user the instance manager
  runs as.
* `OPENSTACK_SANDBOX_SSH_USERNAME` The user to run ansible playbooks as when
  provisioning the sandbox (default: `ubuntu`)
* `INSTANCE_EPHEMERAL_DATABASES` By default, instances use local mysql and mongo
  databases. Set this to False to use external databases instead (default: True)
* `INSTANCE_MYSQL_URL` If using an external mysql database, set its url here
* `INSTANCE_MONGO_URL` If using an external mongo database, set its url here


Migrations
----------

To run database migrations:

    make migrate

The startup commands such as `make run` and `make rundev` check for pending
migrations, and will exit before starting the server if any are found. You can
also check for pending migrations manually with:

    make migration_check


Creating a user
---------------

In order to login to the development server locally you will need to create a
superuser by running:

    honcho run ./manage.py createsuperuser

Once created, you will be able to login with the username and password you set
up.


Run
---

To run the development server:

    make rundev

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
* *websocket*: the websocket server (Tornado)
* *worker*: runs asynchronous jobs (Huey)

Important: the Werkzeug debugger started by the development server allows remote
execution of Python commands. It should *not* be run in production.


Static assets collection
------------------------

The web server started in the development environment also doesn't require
collectstatic to run after each change.

The production environment automatically runs collectstatic on startup, but you
can also run it manually:

    make collectstatic


Running the tests
-----------------

To run the whole test suite (pylint, pyflakes, pep8, unit tests, etc.):

    make test


To run a single test, use `make test_one`:

    make test_one instance.tests.models.test_server

You can also run Prospector, the unit tests, JS tests and integration tests
independently:

    make test_prospector
    make test_unit
    make test_js
    make test_integration

JS tests can be run in your browser for debugging (run `make test_js_web` and
then go to http://localhost:8888/ ), or in a CI manner via selenium and
`jasmine-ci` (run `make test_js`).

Note that the integration tests aren't run by default, as they require a working
OpenStack cluster configured. To run them, create a `.env.integration` file -
your development environment is likely a good starting point:

    cp .env .env.integration


Debug
-----

To access the console, you can use `shell_plus`:

    make shell


Provisioning sandboxes
----------------------

### GitHub pull requests

When configured correctly, the instance manager will automatically provision
sandboxes whenever a pull request is made on GitHub on your configured
`WATCH_FORK`, by members of your `WATCH_ORGANIZATION`.

To customize these sandboxes, you can add a **Settings** section to your pull
request description, using the following format:

    **Settings**
    ```yaml
    # Include extra ansible vars as yaml here
    ```

For example:

    **Settings**
    ```yaml
    EDXAPP_FEATURES:
      ALLOW_HIDING_DISCUSSION_TAB: true
    ```

Note: You need to match the above format exactly.

### Manual provisioning

If you want to provision a sandbox outside of a GitHub pull request, you can do
so from the shell:

```python
from instance.models.instance import SingleVMOpenEdXInstance
from instance.tasks import provision_instance

instance = SingleVMOpenEdXInstance.objects.create(
    sub_domain='dogwood.sandbox',
    name='Dogwood',
    fork_name='edx/edx-platform',
    branch_name='named-release/dogwood',
    configuration_version='named-release/dogwood',
    forum_version='named-release/dogwood',
    notifier_version='named-release/dogwood',
    xqueue_version='named-release/dogwood',
    certs_version='named-release/dogwood',
    ansible_source_repo_url='https://github.com/edx/configuration.git',
)

instance.ansible_extra_settings = """
# Add custom ansible settings here, as yaml
NGINX_ENABLE_SSL: true
"""

instance.save()
provision_instance(instance.pk)
```

To reprovision an instance from the shell, simply run the `provision_instance`
task again:

```python
instance = SingleVMOpenEdXInstance.objects.get(name__contains='...')
provision_instance(instance.pk)
```

To delete an instance, ensuring that all virtual machines are terminated, run:

```python
instance.server_set.terminate()
instance.delete()
```


manage.py
---------

You can also access the Django `manage.py` command directly, using Honcho to
load the environment:

    honcho run ./manage.py <command>


Databases
---------

By default, sandboxes will use local, ephemeral databases that are destroyed
when the sandbox is reprovisioned. If you want to reuse databases, change the
`INSTANCE_EPHEMERAL_DATABASES` setting to False, set up external mysql and mongo
databases and update the `INSTANCE_MYSQL_URL` and `INSTANCE_MONGO_URL` settings
to point to these databases.

When provisioning a sandbox from the GitHub pull request, you can override the
default by including `(ephemeral databases)` or `(persistent databases)` on the
same line as the sandbox domain in the pull request description. For example:

    This pull request adds reticulating splines to the LMS.

    Test it here: pr99.sandbox.example.com (ephemeral databases)
