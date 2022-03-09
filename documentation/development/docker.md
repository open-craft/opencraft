# Docker

This describes how to create an environment for development using Docker.

## Running OCIM in a docker container

First, set your `.env` file as you would normally, but first set the following vars:
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
DEFAULT_INSTANCE_REDIS_URL=...
DEFAULT_MONGO_REPLICA_SET_USER=...
DEFAULT_MONGO_REPLICA_SET_PASSWORD=...
DEFAULT_MONGO_REPLICA_SET_NAME=...
DEFAULT_MONGO_REPLICA_SET_PRIMARY=...
DEFAULT_MONGO_REPLICA_SET_HOSTS=...
REDIS_URL=...
```

```sh
ALLOWED_HOSTS='["*"]'
DATABASE_URL='postgres://opencraft@postgresql/opencraft'
REDIS_URL='redis://redis:6379'
```

Run some initial setup tasks in the backend:

```sh
docker-compose run --rm ocim make migrate
docker-compose run --rm ocim make manage createsuperuser
```

And on the frontend:

```sh
docker-compose run --rm ocim-frontend bash -c 'npm run build-api-client && npm install'
```

Then, launch the stack (detached):

```sh
docker-compose up -d
```

The OCIM UI should be available at <http://localhost:5000>.
The registration UI should be available at <http://localhost:3000>.

To view or follow the logs for any of the running services, use `docker-compose logs`.
For example:

```sh
docker-compose logs -f ocim
```

