# Docker

This describes how to create an environment for development using Docker.

**This is still experimental, using [Vagrant](../installation.md) is much better tested and supported!**

## Running OCIM in a docker container

First, set your `.env` file as you would normally:
```env
DEBUG=True
OPENSTACK_USER='username'
OPENSTACK_PASSWORD='password'
OPENSTACK_TENANT='tenant-name'
OPENSTACK_AUTH_URL='https://auth.cloud.ovh.net/v2.0'
OPENSTACK_REGION='BHS1'
OPENSTACK_SANDBOX_SSH_KEYNAME='keypair-name'
DEFAULT_INSTANCE_BASE_DOMAIN='example.com'
GANDI_API_KEY='api-key'
GITHUB_ACCESS_TOKEN='github-token'
SECRET_KEY='tests'
DEFAULT_INSTANCE_MYSQL_URL=...
DEFAULT_RABBITMQ_API_URL=...
DEFAULT_INSTANCE_RABBITMQ_URL=...
DEFAULT_MONGO_REPLICA_SET_USER=...
DEFAULT_MONGO_REPLICA_SET_PASSWORD=...
DEFAULT_MONGO_REPLICA_SET_NAME=...
DEFAULT_MONGO_REPLICA_SET_PRIMARY=...
DEFAULT_MONGO_REPLICA_SET_HOSTS=...
REDIS_URL=...
```

Start a one-off container for setup of the backend:
```sh
# --rm destroys the container at the end
docker-compose run --rm ocim bash

# then, inside the container...

# initialize datastores
make migrate
# create super user
make manage createsuperuser
# exit the container
exit
```

Then, start another one-off container for setting up the client-facing frontend:
```sh
docker-compose run --rm ocim-frontend bash -c 'npm run build-api-client && npm install'
```

Then, start OCIM:
```sh
docker-compose up
```

The OCIM UI should be available at http://localhost:5000 .
The registration UI should be available at http://localhost:3000 .