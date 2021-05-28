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
    EDXAPP_FEATURES_EXTRA:
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
they will override the variables defined in `instance/models/mixins/openedx_config.py`.

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
