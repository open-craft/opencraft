# Docker

This describes how to create an environment for development using Docker.

## Running OCIM in a docker container

Create `.env` file

```sh
cp .env.test .env
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

**Running make commands**

You can directly run make commands as below:

```sh
docker-compose run --rm ocim make <command>
```

**OR**

Run make commands inside docker container using:

```sh
docker-compose run --rm ocim bash
make <command>
```
