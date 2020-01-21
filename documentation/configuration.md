Configuration
-------------

[Honcho](https://honcho.readthedocs.io/en/latest/) will set up environment
variables defined in the `.env` file at the root of your repository. If you are
using vagrant for development, a basic `.env` file will already have been
created for you, but you will need to add credentials for third-party services
manually in order to run the development server or the integration tests.

The environment variables in `.env` customize the settings from
`opencraft/settings.py` which are loaded via `env()`. For more information about
each setting, see the [list of settings](#application-settings) below, and
[`opencraft/settings.py`](https://github.com/open-craft/opencraft/tree/master/opencraft/settings.py).
As a minimum, you will need to add credentials for OpenStack, Gandi, RabbitMQ, and GitHub.
You can use this example `.env` file as a starting point:

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

* `iam:PutUserPolicy`
* `iam:CreateUser`
* `iam:CreateAccessKey`
* `iam:DeleteUser`
* `iam:DeleteAccessKey`
* `iam:DeleteUserPolicy`

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
* `GANDI_DEFAULT_BASE_DOMAIN`: The base domain owned in the Gandi account if the `DEFAULT_INSTANCE_BASE_DOMAIN`
  its sub-domain. (optional, default: `DEFAULT_INSTANCE_BASE_DOMAIN`).

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

Databases
---------

You must configure external databases that can be used by any app server belonging
to an instance, following these steps:

1. Set up external MySQL and MongoDB databases, making a note of hostname
   and authentication information (username, password) for each one of them.

2. In your `.env` file, set `DEFAULT_INSTANCE_MYSQL_URL` and `DEFAULT_INSTANCE_MONGO_URL`
   to URLs that point to the MySQL and MongoDB servers created in the previous step:


        DEFAULT_INSTANCE_MYSQL_URL='mysql://<user>:<password>@<hostname>:<port>'
        DEFAULT_INSTANCE_MONGO_URL='mongodb://<user>:<password>@<hostname>:<port>'


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
