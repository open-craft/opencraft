# Continuous Integration

This describes aspects of Continuous Integration setup specifically for OpenCraft,
and is of limited interest for external contributors.

## CI specific env file

Because we couldn't find a way to establish DNS/hostname for each container in
circleci, we had to build an additional env file for CI.

Only below variables in `.env.test.ci` differ from `.env.test`.

```sh
# .env.test
DATABASE_URL='postgres://opencraft@postgresql/opencraft'
DEFAULT_INSTANCE_MYSQL_URL='mysql://root:opencraft@mysqldb:3306'
DEFAULT_INSTANCE_MONGO_URL='mongodb://opencraft:opencraft@mongodb:27017'
```

```sh
# .env.test.ci
DATABASE_URL='postgres://localhost/opencraft'
DEFAULT_INSTANCE_MYSQL_URL='mysql://root@127.0.0.1'
DEFAULT_INSTANCE_MONGO_URL='mongodb://127.0.0.1'
```

**Reason**: When using docker-compose locally, we may connect to services by
their names, for example, to connect to postgresql from another container, we
can use a url like this: postgres://opencraft@postgresql/opencraft, but postgres
is only available on localhost inside circleci.

## Cleaning up left-over resources

Test runs (especially failing ones) may occasionally leave behind resources that,
over time, clutter the underlying infrastructure.

To avoid this, there is [a `scheduled-cleanup` CircleCI workflow](https://github.com/open-craft/opencraft/blob/master/circle.yml)
that regularly runs the `cleanup` job.

If necessary (usually when testing changes to it), the job may be run on-demand
by pushing to the `ci-cleanup` branch.
