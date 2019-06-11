OpenCraft Instance Manager
==========================

[![Circle CI](https://img.shields.io/circleci/project/open-craft/opencraft/master.svg)](https://circleci.com/gh/open-craft/opencraft/tree/master) [![Dependency Status](https://gemnasium.com/badges/github.com/open-craft/opencraft.svg)](https://gemnasium.com/github.com/open-craft/opencraft)

The OpenCraft Instance Manager (Ocim) is a Django application to deploy and
manage [Open edX](https://open.edx.org/) sandboxes on
[OpenStack](https://www.openstack.org/) virtual machines. It is primarily
intended for testing new features, and can deploy sandboxes automatically from
GitHub pull requests.

It also includes a web console where you can create new servers and check their status and configuration.

![Ocim's main screen](documentation/ocim_main_screen.png)

Table of Contents
-----------------

- [Using the Ocim web console](#using-the-ocim-web-console)
- [Install](#install)
- [Configure](#configure)
- [Migrations](#migrations)
- [Creating users](#creating-users)
- [Run](#run)
- [Process description](#process-description)
- [Static asset collection](#static-assets-collection)
- [Running the tests](#running-the-tests)
- [Debug](#debug)
- [Provisioning sandboxes](#provisioning-sandboxes)
- [manage.py](#managepy)
- [Databases](#databases)

Using the Ocim web console
--------------------------

This section focuses on how to use the web interface, as opposed to how to install, debug or develop Ocim;
see the following sections for that.

At the left there's a list of instances, and each instance has many appservers.
We can create a new appserver through the **Launch new AppServer** button;
it will automatically get the current configuration from the instance settings
and use it for this server.
After 1 to 2 hours, it will finish and then you need to **activate** the new one
and **deactivate** the old one, to make the load balancer update its configuration
so that the domain name of the instance directs to the new one.
Normally we want just 1 active appserver per instance, but two or more active at once
may be required in some high-resource-utilization cases.
Before activating a server, there's the option to test it through a
basic-auth password-protected link in the "Authenticated Link" section
(the username and password are embedded in the link).
If you want to terminate a VM associated with an App Server, first you must
**deactivate** it and then **terminate**. Notice that only instances with an
associated pull request can have all its App Servers deactivates/terminated.

Sometimes Open edX playbook fails, and then you need to read the log,
which is shown in real-time in the web console.
You can fix the settings and then spawn another server.
Failed and old inactive servers are automatically cleaned up after some configurable amount of days.
An important feature is that Ocim *grants SSH access* to members of a configurable GitHub organization,
so you can always SSH to an appserver's IP, *even if Open edX's deployment failed*, and then debug it.
You can use your GitHub username and key.

To create a new instance, you use Django's admin and you need to fill in the domain name,
the prefixed domain names (for Studio, e-commerce, etc.), the edx-platform/configuration branches to use,
and extra ansible variables to pass to Open edX's playbook (if any).
The instance settings are used for new deployments only
(changing the instance settings doesn't retroactively redeploy appservers).


Install
-------

### Vagrant install

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

### Local install (skip this step if using Vagrant)

If you prefer not to use Vagrant, you can install OpenCraft manually. Refer to
the [Ansible playbooks](https://github.com/open-craft/ansible-opencraft) used
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

Configure
---------

[Honcho](https://honcho.readthedocs.io/en/latest/) will set up environment
variables defined in the `.env` file at the root of your repository. If you are
using vagrant for development, a basic `.env` file will already have been
created for you, but you will need to add credentials for third-party services
manually in order to run the development server or the integration tests.

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
```

You can also configure the environment variables using a YAML file from which
Ansible can load these values. Create a file called ``private.yml`` and use the
following contents as a starting point:

```yaml
OPENCRAFT_ENV_TOKENS:
  SECRET_KEY: '...'
  DATABASE_URL: 'postgres://localhost/opencraft'
  OPENSTACK_USER: 'username'
  OPENSTACK_PASSWORD: 'password'
  OPENSTACK_TENANT: 'tenant-name'
  OPENSTACK_AUTH_URL: 'https://auth.cloud.ovh.net/v2.0'
  OPENSTACK_REGION: 'BHS1'
  OPENSTACK_SANDBOX_SSH_KEYNAME: 'keypair-name'
  DEFAULT_INSTANCE_BASE_DOMAIN: 'example.com'
  GANDI_API_KEY: 'api-key'
  GITHUB_ACCESS_TOKEN: 'github-token'
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

[Configure the client](https://web.archive.org/web/20161105104308/https://docs.openstack.org/user-guide/common/cli-set-environment-variables-using-openstack-rc.html),
with the same OpenStack credentials that you used in the `.env` file and run:

    openstack keypair create --public-key ~/.ssh/id_rsa.pub KEY_NAME

where `KEY_NAME` is the name used to identify this key pair in OpenStack. The
`OPENSTACK_SANDBOX_SSH_KEYNAME` setting in your `.env` file should be set to
this name.

### OpenStack images

Open edX is currently designed to run on Ubuntu 16.04. Your OpenStack host may
already have an image available for this version of Ubuntu. You can manage
OpenStack images using `glance`:

    pip install python-glanceclient

You can check the images available with your host using:

    glance image-list

For maximum compatibility we recommend the
[official Ubuntu cloud image](https://cloud-images.ubuntu.com/xenial/current/).
If this image is not available with your host, you can fetch it and add to
OpenStack using `glance`:

    wget https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img
    glance image-create \
      --disk-format=qcow2 \
      --container-format=bare \
      --file xenial-server-cloudimg-amd64-disk1.img \
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
network security group, which provides a firewall that limits what
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

### AWS S3 Storage

Permissions required for master AWS account are:
* iam:PutUserPolicy
* iam:CreateUser
* iam:CreateAccessKey
* iam:DeleteUser
* iam:DeleteAccessKey
* iam:DeleteUserPolicy

Required settings:
* `INSTANCE_STORAGE_TYPE`: A choice between "s3", "swift" and "filesystem" (default: "swift")
* `AWS_ACCESS_KEY_ID`: AWS Access Key Id from account with accesses listed above.
* `AWS_SECRET_ACCESS_KEY`: AWS Secret Key with accesses listed above.
* `AWS_S3_BUCKET_PREFIX`: Prefix used for bucket naming (default: "ocim")
* `AWS_IAM_USER_PREFIX`: Prefix used for IAM username (default: "ocim")

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
* `DEFAULT_RABBITMQ_API_URL`: The full API URL (including the protocol, port, and basic auth)
  to the RabbitMQ server which will be used to manage vhosts and users for instances. E.g.,
  `https://admin:admin_password@rabbitmq.example.com:15671`
* `DEFAULT_INSTANCE_RABBITMQ_URL`: The RabbitMQ AMQPS URI to be used by instances. E.g.,
  `amqps://rabbitmq.example.com:5671`

### DNS settings

* `DEFAULT_INSTANCE_BASE_DOMAIN`: Instances are created as subdomains of this domain,
  e.g. `example.com` (required)
* `DEFAULT_LMS_PREVIEW_DOMAIN_PREFIX`: String to prepend to internal LMS domain when
  generating the LMS preview domain (default: `"preview-"`)
* `DEFAULT_STUDIO_DOMAIN_PREFIX`: String to prepend to internal LMS domain when
  generating the Studio domain (default: `"studio-"`)
* `DEFAULT_ECOMMERCE_DOMAIN_PREFIX`: String to prepend to internal LMS domain when
  generating the ecommerce domain (default: `"ecommerce-"`)
* `DEFAULT_DISCOVERY_DOMAIN_PREFIX`: String to prepend to internal LMS domain when
  generating the Course Discovery domain (default: `"discovery-"`)
* `GANDI_API_KEY`: Your Gandi API key (required)

### GitHub settings

* `GITHUB_ACCESS_TOKEN`: Your GitHub access token (required). Get it from
  https://github.com/settings/tokens, and enable the `read:org` and
  `read:user` scopes on the token.

### New Relic settings

* `NEWRELIC_LICENSE_KEY`: Your New Relic license key. If set, New Relic server
  and application monitoring will be enabled.
* `NEWRELIC_ADMIN_USER_API_KEY`: An API key for a New Relic admin user. If set,
  Synthetics availability monitoring will be enabled. Downtime alerts are sent
  to the email addresses in `ADMINS`.

## Prometheus settings

* `NODE_EXPORTER_PASSWORD`: The basic auth password needed to access the node exporter.

## Consul settings

* `CONSUL_ENCRYPT`: The encryption key used to gossip in a Consul cluster.
* `CONSUL_SERVERS`: The list of server agents in the Consul cluster.

## Filebeat settings

* `FILEBEAT_LOGSTASH_HOSTS`: The Logstash host to forward logs to.
* `FILEBEAT_CA_CERT`: The CA certificate used to verify the Logstash host.
* `FILEBEAT_CERT`: The TLS certificate used for client authentication against Logstash.
* `FILEBEAT_KEY`: The TLS private key used for client authentication against Logstash.
* `FILEBEAT_COMMON_PROSPECTOR_FIELDS`: Common fields for all Filebeat prospectors.

### Sandbox settings

* `OPENSTACK_SANDBOX_FLAVOR`: A json string specifying the instance flavor to use
  (default: `{"ram": 4096, "disk": 40}`)
* `OPENSTACK_SANDBOX_BASE_IMAGE`: A json string specifying the base image to use
  (default: `{"name": "Ubuntu 16.04"}`)
* `OPENSTACK_SANDBOX_SSH_KEYNAME`: The name of the default ssh key pair used to
  connect to sandbox instances (default: `opencraft`). This key pair should be
  [registered with OpenStack](http://docs.openstack.org/user-guide/cli_nova_configure_access_security_for_instances.html)
  first, and should be the default ssh key for the user the instance manager
  runs as.
* `OPENSTACK_SANDBOX_SSH_USERNAME`: The user to run ansible playbooks as when
  provisioning the sandbox (default: `ubuntu`)
* `DEFAULT_INSTANCE_MYSQL_URL`: The external MySQL database server to be used
  by Open edX instances created via the instance manager. The database server
  will be represented as an instance of the `MySQLServer` model in the database.
  It is possible to create multiple instances of that model. This setting
  exists mainly to make it easier to add a MySQL database server in testing
  and development environments.  It is mandatory to set this setting to run the
  initial migrations.
* `DEFAULT_INSTANCE_MONGO_URL`: The external MongoDB database server to be used
  by Open edX instances created via the instance manager. The database server
  will be represented as an instance of the `MongoDBServer` model in the database.
  It is possible to create multiple instances of that model. This setting
  exists mainly to make it easier to add a MongoDB database server in testing
  and development environments.  It is mandatory to set this setting to run the
  initial migrations.

#### MongoDB using a replica set by default

Unset `DEFAULT_INSTANCE_MONGO_URL` and set the following settings:

* `DEFAULT_MONGO_REPLICA_SET_NAME`: Name of the replica set as setup in MongoDB.
* `DEFAULT_MONGO_REPLICA_SET_USER`: User used to connect to the MongoDB Servers.
* `DEFAULT_MONGO_REPLICA_SET_PASSWORD`: Password used to connect to the MongoDB Servers.
* `DEFAULT_MONGO_REPLICA_SET_PRIMARY`: Hostname of primary replica set instance.
* `DEFAULT_MONGO_REPLICA_SET_HOSTS`: All hosts on the replica set (including the primary).

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
* `EDX_WORKERS_ENABLE_CELERY_HEARTBEATS`: Switch to enable/disable celery
  heartbeats used to detect connection drops. Disabling heartbeats can have a
  drastic reduction RabbitMQ usage. This setting sets
  `worker_django_enable_heartbeats` and `EDXAPP_CELERY_HEARTBEAT_ENABLED` on
  supported playbooks. Defaults to `False`.

Migrations
----------

To run database migrations:

    make migrate

The startup commands such as `make run` and `make run.dev` check for pending
migrations, and will exit before starting the server if any are found. You can
also check for pending migrations manually with:

    make migrations.check

Creating users
--------------

### Superusers

In order to login to the development server locally you will need to create a
superuser by running:

    make manage createsuperuser

Once created, you will be able to login with the username and password you set
up.

Superusers can manage all instances and use all APIs.

### Instance Manager users

Instance manager users can manage instances and use the API, but are not permitted in the Admin area.
They are limited to manage instances of their own organization.

To create an instance manager user:

    make shell

    In [1]: from django.contrib.auth.models import User, Permission
    In [2]: from django.contrib.contenttypes.models import ContentType
    In [3]: content_type = ContentType.objects.get_for_model(InstanceReference)
    In [4]: permission = Permission.objects.get(content_type=content_type, codename='manage_own')
    In [5]: user = User.objects.create(username='instance_manager', password='password')
    In [6]: user.user_permissions.add(permission)
    In [7]: user.save()

And set `Organization` and `UserProfile` to the right values.

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

Provisioning sandboxes
----------------------

### GitHub pull requests

When configured correctly, the instance manager can automatically provision
sandboxes whenever a pull request is made on GitHub. You can choose which
repositories and organization to watch by creating in admin or shell a
`WatchedFork` object with the name of your fork (e.g. `edx/edx-platform`).

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

Another option to customize sandboxes is to write the settings as a field inside
the `WatchedFork`: `configuration_extra_settings`. These settings will be applied
to all pull requests for that repository, without having to write a **Settings**
section in each PR. If there is a **Settings** section, it will be combined with
the `WatchedFork` settings, with the PR settings always having precedence.
The `configuration_source_repo_url`, `configuration_version` and `openedx_release`
from the `WatchedFork` provide a default value for all PRs of that fork, and can
also be overriden in the PR body through the `edx_ansible_source_repo`,
`configuration_version` and `openedx_release` variables respectively.

### Manual provisioning

If you want to create an instance outside of a GitHub pull request, you can do
so from the shell. There are two options:

**Factory methods**

OpenCraft IM provides two factory methods for creating instances (the
following lines should run via `make shell`):

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
)

# Optionally, set custom ansible variables/overrides:
instance.configuration_extra_settings = """
NGINX_ENABLE_SSL: true
"""
instance.save()
```

Once the instance is created, use the web UI to review the instance
configuration, then use the "Launch new AppServer" button to provision a server.

Once the server is ready (refresh the page to check), select it in the UI and click "Activate this app
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
with the updated settings, wait, refresh the page to check if it's ready, and
click "Activate this app server" to use the new server when it's ready.

**To terminate all VMs associated with an instance**, but still preserve the
information about the AppServers and their configuration, run:

```python
for appserver in instance.appserver_set.all():
    appserver.terminate_vm()
```

**To delete an instance in production**, use the `archive()` method. The `archive()`
method will terminate all associated AppServers, remove DNS entries, disable monitoring,
and remove instance from the UI, but will keep data in databases and SWIFT/S3 storage intact:

```python
instance.archive()
```

**To completely delete an instance in development**, use the `delete()` method, which
works just like `archive()` except that it also destroys all data (MySQL, mongo, SWIFT/S3):

```python
instance.delete()
```

Use `delete(ignore_errors=True)` in case some of the resources related
to an instance were deleted or modified and "forcing" deletion is necessary.

It is possible to ignore errors for specific resources when deleting an instance:

- `delete(ignore_mysql_errors=True)` to ignore MySQL errors.
- `delete(ignore_mongo_errors=True)` to ignore Mongo errors.
- `delete(ignore_rabbitmq_errors=True)` to ignore RabbitMQ errors.

> **Note:** Any errors raised and its stacktrace will be logged in case
> there's need for more information.

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

**`instance_redeploy`**: Redeploy appservers in bulk, optionally making updates
to apply upgrades or settings changes prior to redeployment.  Appservers are
spawned in batches, and successful redeployments will be automatically
activated.  To see the options available, run:

    make manage "instance_redeploy --help"

Keep track of the number of redeployments running in a batch. If it is larger
than the number of workers available, then you will run into issues. You can
check the number of regular workers with ``echo $WORKERS`` and the number of
low-priority workers with ``echo $WORKERS_LOW_PRIORITY``. If those values are
not set in the environment, then they have the default values defined in the
[Makefile](Makefile).

To ensure that people are still able to use the website to activate/deactivate
or launch AppServers you should probably run the redeployment command in the
low-priority queue.  You can do that by prepending ``HUEY_QUEUE_NAME=opencraft_low_priority``
before the redeployment command. For example:

    HUEY_QUEUE_NAME=opencraft_low_priority make manage "instance_redeploy ..."

Databases
---------

You must configure external databases that can be used by any app server belonging
to an instance, following these steps:

1. Set up external MySQL and MongoDB databases, making a note of hostname
   and authentication information (username, password) for each one of them.

2. In your `.env` file, set `DEFAULT_INSTANCE_MYSQL_URL` and `DEFAULT_INSTANCE_MONGO_URL`
   to URLs that point to the MySQL and MongoDB servers created in the previous step:

   ```env
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

### Configuring ecommerce and Course Discovery

By default, instances are not provisioned with either ecommerce or the Course Discovery
service. However, support is available to manually enable those services. To do so:

* Ensure that the [`refresh_course_metadata` cron task](https://github.com/open-craft/configuration/blob/c1e576eabefea82d21d7785810126e39752cd14e/playbooks/roles/discovery/tasks/main.yml)
  is added to the ansible discovery tasks.
* Set these extra variables on the instance:
  ```yaml
  SANDBOX_ENABLE_DISCOVERY: yes
  SANDBOX_ENABLE_ECOMMERCE: yes
  DISCOVERY_VERSION: 'open-release/ginkgo.1'
  nginx_discovery_gunicorn_hosts:
      - "127.0.0.1"
  COMMON_HOSTNAME: "your-site-name"
  ECOMMERCE_PAYMENT_PROCESSOR_CONFIG:
      your-partner-code:
        paypal:
          ...
  ```

Notes:

* We need to set the `COMMON_HOSTNAME` to something other than the FQDN, so
  that API requests made on the server can be properly routed through the load
  balancer-terminated SSL connection.  This is required because, by default, the
  appserver's FQDN refers to localhost, which doesn't understand SSL.
* The [`ECOMMERCE_PAYMENT_PROCESSOR_CONFIG`](https://github.com/edx/configuration/blob/d68bf51d7b8403bdad09dc764af5ebafe16d7309/playbooks/roles/ecommerce/defaults/main.yml#L103)
  should contain the payment processors and their keys.

Once the spawn is complete, you'll need to take the following steps to finish setup
(these are one-time actions that are stored in the database):

1. Create/choose a staff user to use for the OAuth2 clients.
   Ensure the staff user has a user profile associated (i.e. set a Full Name).
1. In Django Admin > OAuth2 > Clients, there should already be clients created
   for ecommerce and discovery.
   If not, [create and register new clients](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html#configure-edx-openid-connect-oidc)
   for each service.  You'll need the client IDs and client secrets for the next
   steps.
   Ensure that both clients are attached to the staff user updated above.
1. In the ecommerce env, add a Site, Partner, and Site Configuration as per the
   instructions in the [edX ecommerce docs](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html#add-another-site-partner-and-site-configuration).
   Use the partner code from `ECOMMERCE_PAYMENT_PROCESSOR_CONFIG`.
1. In the discovery env, configure a partner using
   [`create_or_update_partner`](https://github.com/edx/course-discovery/blob/master/course_discovery/apps/core/management/commands/create_or_update_partner.py).
   Use the same partner code as what you used for ecommerce.
1. [Configure LMS to use ecommerce](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html#switch-from-shoppingcart-to-e-commerce)

Test your configuration:

1. Verify the OIDC login for both services:

    https://ecommerce-<your-instance>.opencraft.hosting/login
    https://discovery-<your-instance>.opencraft.hosting/login

1. Verify that the discovery cronjob runs without errors:

    ```sh
    sudo -s -c . /edx/app/discovery/discovery_env; /edx/bin/manage.discovery refresh_course_metadata
    ```

Useful references:

* [Adding E-Commerce to the Open edX Platform](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html)
* [edX Discovery Service](http://edx-discovery.readthedocs.io/)
* [Setup Discovery Sandbox](https://openedx.atlassian.net/wiki/spaces/EDUCATOR/pages/162488548/Setup+Discovery+Sandbox)
