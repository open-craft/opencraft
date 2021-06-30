# Docker

This describes how to create an environment for development using Docker.

**This is still experimental, using [Vagrant](../installation.md) is much better tested and supported!**

## Running OCIM in a docker container

First, set your `.env` file as you would normally,
but set the following vars:

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
