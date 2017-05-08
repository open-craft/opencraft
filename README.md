OpenCraft Instance Manager
==========================

[![Circle CI](https://img.shields.io/circleci/project/open-craft/opencraft/master.svg)](https://circleci.com/gh/open-craft/opencraft/tree/master) [![Dependency Status](https://gemnasium.com/badges/github.com/open-craft/opencraft.svg)](https://gemnasium.com/github.com/open-craft/opencraft)

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

This will provision a virtual machine running Ubuntu 16.04, set up local
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
Instructions based on Ubuntu 16.04.

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
add credentials for OpenStack, Gandi, RabbitMQ, and GitHub. You can use this example `.env`
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
DEFAULT_INSTANCE_BASE_DOMAIN='example.com'
GANDI_API_KEY='api-key'
GITHUB_ACCESS_TOKEN='github-token'
WATCH_ORGANIZATION='github-org'
RABBITMQ_API_URL='https://rabbitmq-dev.opencraft.hosting:15671'
RABBITMQ_ADMIN_USERNAME='admin'
RABBITMQ_ADMIN_PASSWORD='changeme'
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
OpenStack. Make sure the nova command line client is installed (it should already
be the case from the OpenCraft IM python environment):

    pip install python-openstackclient

[Configure the client with your OpenStack credentials](http://docs.openstack.org/cli-reference/common/cli_set_environment_variables_using_openstack_rc.html),
then run:

    openstack keypair create --public-key ~/.ssh/id_rsa.pub KEY_NAME

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

### OpenStack Security Groups

Every VM used to host Open edX will automatically be added to an OpenStack
network security group, which is provides a firewall that limits what 
ports/services on the VM are exposed to the Internet. The security group will
automatically be created and managed by OpenCraft IM.

Instances of Open edX can also be assigned additional security groups.
Typically, these additional security groups would not contain any rules; they
are instead used for things like granting access to a specific database server.
(e.g. add an additional security group called `allow-mysql-access` to the Open
edX instance; it does not need to contain any rules. Then, on your MySQL server,
edit its security group rules to only allow access to VMs in the
`allow-mysql-access` security group.)

### Application settings

* `DEBUG`: Turn on debug mode. Use in development only (default: False)
* `SECRET_KEY`: Set this to something unique and keep it secret (required)
* `DATABASE_URL`: Your database, e.g. `postgres://localhost/opencraft` (required)
* `REDIS_URL`: (default: `redis://localhost:6379/`)
* `HUEY_ALWAYS_EAGER`: Set to True to run huey tasks synchronously, in the web
  process. Use in development only (default: False)
* `HUEY_QUEUE_NAME`: The name of the Huey task queue.  This setting can be used
  to run multiple separate worker queues, e.g. one for the web server and one
  for batch jobs started from the Django shell.
* `LOGGING_ROTATE_MAX_KBYTES`: The max size of each log file (in KB, default: 10MB)
* `LOGGING_ROTATE_MAX_FILES`: The max number of log files to keep (default: 60)
* `SUBDOMAIN_BLACKLIST`: A comma-separated list of subdomains that are to be
  rejected when registering new instances
* `BETATEST_EMAIL_SENDER`: Sender of the emails related to the beta test
* `BETATEST_EMAIL_SIGNATURE`: The email signature to be used for beta test emails

### OpenStack credentials

* `OPENSTACK_USER`: Your openstack username (required)
* `OPENSTACK_PASSWORD`: Your openstack password (required)
* `OPENSTACK_TENANT`: Your openstack tenant name (required)
* `OPENSTACK_AUTH_URL`: Your openstack auth url (required)
* `OPENSTACK_REGION`: The openstack region to deploy sandboxes in (required)

### Load balancer settings
* `DEFAULT_LOAD_BALANCING_SERVER`: The load-balancing server to be used in the
  form `ssh_username@domain.name`.  The server will be represented as an
  instance of the LoadBalancingServer model in the database.  It is possible to
  create multiple instances of that model.  This setting exists mainly to make
  it easier to add a load-balancing server in testing and development
  environments.
* `LOAD_BALANCER_FRAGMENT_NAME_PREFIX`: A prefix prepended to the filename of
  the configuration fragments added to the load balancer.  This serves mainly
  the purpose of making the fragments easier to recognise, and it should be set
  to a value identifying the instance manager installation.
* `PRELIMINARY_PAGE_SERVER_IP`: The IP address requests will be relayed to by
  the load balancer when no AppServer is active (e.g. during the deployment of
  the first AppServer.)  This can point to a static page informing the user that
  the instance is currently being deployed.

### RabbitMQ settings
* `RABBITMQ_API_URL`: The full API URL (including the protocol and port) to the
  RabbitMQ server which will be used to manage vhosts and users for instances.
* `RABBITMQ_ADMIN_USERNAME`: The username of an account which has the permission to
  create and delete vhosts and users.
* `RABBITMQ_ADMIN_PASSWORD`: The corresponding password of the admin account.
* `INSTANCE_RABBITMQ_HOST`: The RabbitMQ host to be used by instances.
* `INSTANCE_RABBITMQ_PORT`: The RabbitMQ port to be used by instances.

### DNS settings

* `DEFAULT_INSTANCE_BASE_DOMAIN`: Instances are created as subdomains of this domain,
  e.g. `example.com` (required)
* `DEFAULT_LMS_PREVIEW_DOMAIN_PREFIX`: String to prepend to internal LMS domain when
  generating the LMS preview domain (default: `"preview-"`)
* `DEFAULT_STUDIO_DOMAIN_PREFIX`: String to prepend to internal LMS domain when
  generating the Studio domain (default: `"studio-"`)
* `GANDI_API_KEY`: Your Gandi API key (required)

### GitHub settings

* `GITHUB_ACCESS_TOKEN`: Your GitHub access token (required). Get it from
  https://github.com/settings/tokens
* `WATCH_ORGANIZATION`: The organization to watch (required). The instance
  manager will automatically set up sandboxes for pull requests made by members
  of this organization.
* `WATCH_FORK`: Sandboxes are created for pull requests made against this fork
  (default: `edx/edx-platform`)

### New Relic settings

* `NEWRELIC_LICENSE_KEY`: Your New Relic license key. If set, New Relic server
  and application monitoring will be enabled.
* `NEWRELIC_ADMIN_USER_API_KEY`: An API key for a New Relic admin user. If set,
  Synthetics availability monitoring will be enabled. Downtime alerts are sent
  to the email addresses in `ADMINS`.

### Sandbox settings

* `OPENSTACK_SANDBOX_FLAVOR`: A json string specifying the instance flavor to use
  (default: `{"ram": 4096, "disk": 40}`)
* `OPENSTACK_SANDBOX_BASE_IMAGE`: A json string specifying the base image to use
  (default: `{"name": "Ubuntu 12.04"}`)
* `OPENSTACK_SANDBOX_SSH_KEYNAME`: The name of the default ssh key pair used to
  connect to sandbox instances (default: `opencraft`). This key pair should be
  [registered with OpenStack](http://docs.openstack.org/user-guide/cli_nova_configure_access_security_for_instances.html)
  first, and should be the default ssh key for the user the instance manager
  runs as.
* `OPENSTACK_SANDBOX_SSH_USERNAME`: The user to run ansible playbooks as when
  provisioning the sandbox (default: `ubuntu`)
* `INSTANCE_EPHEMERAL_DATABASES`: By default, instances use local mysql and mongo
  databases. Set this to False to use external databases instead (default: True)
* `DEFAULT_INSTANCE_MYSQL_URL`: The external MySQL database server to be used
  by instances configured not to use ephemeral databases. The database server
  will be represented as an instance of the `MySQLServer` model in the database.
  It is possible to create multiple instances of that model. This setting
  exists mainly to make it easier to add a MySQL database server in testing
  and development environments.  It is mandatory to set this setting to run the
  initial migrations.
* `DEFAULT_INSTANCE_MONGO_URL`: The external MongoDB database server to be used
  by instances configured not to use ephemeral databases. The database server
  will be represented as an instance of the `MongoDBServer` model in the database.
  It is possible to create multiple instances of that model. This setting
  exists mainly to make it easier to add a MongoDB database server in testing
  and development environments.  It is mandatory to set this setting to run the
  initial migrations.

### External SMTP service settings

If you want to use an external SMTP service for sending email from app servers,
set the following configuration variables:

* `INSTANCE_SMTP_RELAY_HOST`: External SMTP host
* `INSTANCE_SMTP_RELAY_PORT`: External SMTP port
* `INSTANCE_SMTP_RELAY_USERNAME`: External SMTP provider username
* `INSTANCE_SMTP_RELAY_PASSWORD`: External SMTP provider password
* `INSTANCE_SMTP_RELAY_SENDER_DOMAIN`: When using external SMTP provider, email
  From addresses are rewritten to use the specified sender domain, which should
  be accepted by the external SMTP host. Defaults to the value of
  `DEFAULT_INSTANCE_BASE_DOMAIN`: setting.

### Open edX specific settings

* `DEFAULT_OPENEDX_RELEASE`: Set this to a release tag like
  `named-release/dogwood` to specify the default release of Open edX to use.
  This setting becomes the default value for `edx_platform_version`,
  `forum_version`, `notifier_version`, `xqueue_version`, and `certs_version` so
  it should be a git branch or tag that exists in all of those repositories.
* `DEFAULT_CONFIGURATION_REPO_URL`: The repository containing the Open edX
  Ansible scripts to use. Defaults to
  `https://github.com/edx/configuration.git`.
* `DEFAULT_CONFIGURATION_VERSION`: The branch/tag/commit from the configuration
  repository to use by default. Normally this does not need to be set; if it is
  not set, the value of `DEFAULT_OPENEDX_RELEASE` will be used.
* `DEFAULT_FORK`: The fork of `edx-platform` to use by default. Defaults to the
  main repository, `edx/edx-platform`.
* `OPENEDX_RELEASE_STABLE_REF`: Set this to a tag or branch for a stable Open
  edX release. It is used as a default value for the `openedx_release` field
  when creating production instances.
* `STABLE_EDX_PLATFORM_REPO_URL`: The edx-platform repo used by default for
  production instances.
* `STABLE_EDX_PLATFORM_COMMIT`: The edx-platform commit ref used by default for
  production instances.  Defaults to OPENEDX_RELEASE_STABLE_REF.
* `STABLE_CONFIGURATION_REPO_URL`: The configuration repo used by default for
  production instances.
* `STABLE_CONFIGURATION_VERSION`: The configuration commit ref used by default
  for production instances.  Defaults to OPENEDX_RELEASE_STABLE_REF.
* `OPENEDX_APPSERVER_SECURITY_GROUP_NAME`: The name of an OpenStack network
  security group to use for the Open edX VMs which run the LMS/CMS. Defaults to
  `edxapp-appserver`. This security group will be automatically created and
  managed by OpenCraft IM; any changes made to it manually will be lost.
* `OPENEDX_APPSERVER_SECURITY_GROUP_RULES`: This specifies the firewall rules
  that the above security group will have. The default allows ingress on ports
  22, 80, and 443 only.

Migrations
----------

To run database migrations:

    make migrate

The startup commands such as `make run` and `make rundev` check for pending
migrations, and will exit before starting the server if any are found. You can
also check for pending migrations manually with:

    make migration_check


Creating users
--------------

### Superusers

In order to login to the development server locally you will need to create a
superuser by running:

    make manage createsuperuser

Once created, you will be able to login with the username and password you set
up.

### Instance Manager users

Instance manager users can manage instances and use the API, but are not permitted in the Admin area.

To create an instance manager user:

    make shell

    In [1]: from django.contrib.auth.models import User, Permission
    In [2]: from django.contrib.contenttypes.models import ContentType
    In [3]: content_type = ContentType.objects.get_for_model(InstanceReference)
    In [4]: permission = Permission.objects.get(content_type=content_type, codename='manage_all')
    In [5]: user = User.objects.create(username='instance_manager', password='password')
    In [6]: user.user_permissions.add(permission)
    In [7]: user.save()

### Staff users

Staff users cannot manage instances or use the API, but are permitted in the
Admin area.

To create a staff user:

    make shell

    In [1]: from django.contrib.auth.models import User
    In [2]: user = User.objects.create(username='staff_user', password='password')
    In [3]: user.is_staff = True
    In [4]: user.save()


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

JS tests can be run in your browser for debugging (run `make test_instance_js_web`
or `make test_registration_js_web` and then go to http://localhost:8888/), or in a
CI manner via selenium and `jasmine-ci` (run `make test_js`).

Note that the integration tests aren't run by default, as they require a working
OpenStack cluster configured. To run them, create a `.env.integration` file -
your development environment is likely a good starting point:

    cp .env .env.integration


There is also a cleanup routine intended for use by CI services to check for and
clean up any dangling OpenStack VMs past a certain age threshold. While it isn't
necessary in the usual case, old integration tests that were killed without cleanup
can be cleaned up after four hours by running the make target:

    make test_integration_cleanup

The age threshold for the cleanup script defaults to four hours, but this can be
adjusted by setting `INSTANCE_AGE_THRESHOLD` to a number (in seconds) in the
`.env.integration` file.

Note that, if executing locally and with the same environment as Circle CI, setting
the `INSTANCE_AGE_THRESHOLD` to a number too low may result in interrupted
integration test builds on Circle CI.


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

If you want to create an instance outside of a GitHub pull request, you can do
so from the shell. There are two options:

**Factory methods**

OpenCraft IM provides two factory methods for creating instances:

```python
from instance.factories import instance_factory, production_instance_factory

# Creating an instance with defaults appropriate for sandboxes:
instance = instance_factory(name="Sandbox instance", sub_domain="sandbox")

# Creating an instance with defaults appropriate for production:
production_instance = production_instance_factory(name="Production instance", sub_domain="production")
```

The only mandatory keyword argument for both functions is `sub_domain`.
You can use additional keyword arguments to pass in non-default values
for any field that is defined on the `OpenEdXInstance` model.
Since both functions return a newly created instance in the form of an
`OpenEdXInstance` object, you can also customize field values later on:

```python
instance.email = 'myname@opencraft.com'
instance.configuration_version = 'named-release/dogwood'
instance.save()
```

If you pass custom `configuration_extra_settings` to `production_instance_factory`,
they will be merged with the settings in [prod-vars.yml](https://github.com/open-craft/opencraft/blob/master/instance/templates/instance/ansible/prod-vars.yml).
Settings that you pass in will take precedence over settings in prod-vars.yml,
that is, if a variable is present in both `configuration_extra_settings` and prod-vars.yml,
the instance manager will use the value from `configuration_extra_settings` for it.

**Django API**

You can also use the Django API to create an instance:

```python
from instance.models.openedx_instance import OpenEdXInstance

instance = OpenEdXInstance.objects.create(
    name='Dogwood sandbox',
    sub_domain='dogwood',
    # The rest of the parameters are all optional:
    email='myname@opencraft.com',
    openedx_release='named-release/dogwood',
    configuration_version='named-release/dogwood',
    configuration_source_repo_url='https://github.com/edx/configuration.git',
    configuration_extra_settings='',
    use_ephemeral_databases=False,
)

# Optionally, set custom ansible variables/overrides:
instance.configuration_extra_settings = """
NGINX_ENABLE_SSL: true
"""
instance.save()
```

Once the instance is created, use the web UI to review the instance
configuration, then use the "Launch new AppServer" button to provision a server.

Once the server is ready, select it in the UI and click "Activate this app
server". (You can also do this in advance, during provisioning, if you want the
DNS updated sooner and aren't concerned about the DNS pointing to a potentially
broken server, in the case the provisioning should fail.)

**To change an instance's parameters**, if that instance is not controlled by a pull
request:

First, note the instance's ID (will be in the URL of that instance in
the web UI, or get it in the shell as `instance.ref.id`). Then, load the
instance, make changes, and save:

```python
instance = InstanceReference.objects.get(id=20).instance
# Update settings of instance:
instance.edx_platform_commit = 'master'
# Save:
instance.save()
```

Then use the "Launch new AppServer" button in the web UI to provision a server
with the updated settings, and click "Activate this app server" to use the new
server when it's ready.

**To terminate all VMs associated with an instance**, but still preserve the
information about the AppServers and their configuration, run:

```python
for appserver in instance.appserver_set.all():
    appserver.terminate_vm()
```

**To delete an instance in production**, use the `archive()` method. The `archive()`
method will terminate all associated AppServers, remove DNS entries, disable monitoring,
and remove instance from the UI, but will keep data in databases and SWIFT storage intact:

```python
instance.archive()
```

**To completely delete an instance in development**, use the `delete()` method, which
works just like `archive()` except that it also destroys all data (MySQL, mongo, SWIFT):

```python
instance.delete()
```

**Do not use delete() in production!**

manage.py
---------

You can also access the Django `manage.py` command directly, using Honcho to
load the environment:

    make manage <command>

Or run any command using the application environment:

    honcho run ./manage.py <command>

### Available commands

**`activity_csv`**: Collect and produce a CSV containing usage information from
all *active app servers*. The CSV will be printed to `stdout` by default, but an
output file can be specified by using the `--out` flag.

    make manage "activity_csv --out activity_report.csv"


Databases
---------

By default, instances will use local, ephemeral databases that are destroyed
when app servers belonging to an instance are terminated. If you want to use
external databases that can be used by any app server belonging to an instance,
follow these steps:

1. Change the `INSTANCE_EPHEMERAL_DATABASES` setting to False. Note that this is
   only necessary if you want instances to use persistent databases by default.
   If you only want a specific instance to use persistent databases, simply set
   the value of the `use_ephemeral_databases` field to `True` and save the instance
   (cf. below).

2. Set up external mysql and mongo databases, making a note of hostname
   and authentication information (username, password) for each one of them.

3. In your `.env` file, set `DEFAULT_INSTANCE_MYSQL_URL` and `DEFAULT_INSTANCE_MONGO_URL`
   to URLs that point to the MySQL and MongoDB servers created in the previous step:

   ```
   DEFAULT_INSTANCE_MYSQL_URL='mysql://<user>:<password>@<hostname>:<port>'
   DEFAULT_INSTANCE_MONGO_URL='mongodb://<user>:<password>@<hostname>:<port>'
   ```

   Note that:

   * `<user>` must have necessary permissions to create databases and users,
     and to grant privileges on the MySQL/MongoDB server.

   * `<hostname>` can be an IP address.

   * `<port>` is optional. It defaults to `3306` for MySQL databases,
     and to `27017` for MongoDB databases.

   The next time you create an instance, the instance manager will automatically
   create a `MySQLServer` and a `MongoDBServer` using the values of the
   `DEFAULT_INSTANCE_MYSQL_URL` and `DEFAULT_INSTANCE_MONGO_URL` settings
   and assign it to the instance.

   **Alternatively**, you can skip setting `DEFAULT_INSTANCE_MYSQL_URL` and `DEFAULT_INSTANCE_MONGO_URL`
   and create `MySQLServer` and `MongoDBServer` objects yourself via the shell or via the Django admin.

   ```python
   from instance.models.database_server import MySQLServer, MongoDBServer

   MySQLServer.objects.create(
       hostname='<hostname>',
       user='<username>',
       password='<password>',
       port=<port>,
   )

   MongoDBServer.objects.create(
       hostname='<hostname>',
       user='<username>',
       password='<password>',
       port=<port>,
   )
   ```

   You can create as many `MySQLServer` and `MongoDBServer` objects as you like.
   If there are multiple servers of a given type to choose from, the instance manager
   will randomly select and assign one of them when you create a new instance.

When the instance manager provisions an app server for an instance that uses persistent databases,
it will automatically add the necessary settings on the associated external database server
to enable the app server to read and store application data. It will also add any information
that is necessary for connecting to the database server to the app server configuration.

Each instance controls its own set of databases on the external database servers,
so it is fine for multiple instances to use the same MySQL and MongoDB database servers.
Set up multiple database servers if the instance manager controls a large number of instances,
or if individual instances receive a large amount of traffic.

### Controlling persistence settings from PRs

When provisioning an instance from a GitHub pull request, you can override the
default behavior (as specified by `INSTANCE_EPHEMERAL_DATABASES`) by including
`(ephemeral databases)` or `(persistent databases)` on the same line
as the instance domain in the pull request description. For example:

    This pull request adds reticulating splines to the LMS.

    Test it here: pr99.sandbox.example.com (ephemeral databases)
