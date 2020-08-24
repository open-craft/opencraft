## Configuring Ecommerce and Course Discovery

By default, instances are not provisioned with either Ecommerce or the Course Discovery service. However, support is available to manually enable those services.

Running Course Discovery requires a separate, persistent VM to be deployed to host ElasticSearch, for performance and deployment reasons.

### Ocim instance extra configuration

*  Ensure that the [`refresh_course_metadata` cron task](https://github.com/open-craft/configuration/blob/c1e576eabefea82d21d7785810126e39752cd14e/playbooks/roles/discovery/tasks/main.yml)
   is added to the ansible discovery tasks. If using a configuration revision that doesn't include this, the following extra cronjob can be added to extra configuration:

```yaml
# must add as root cronjob, even though we want to run the task as the discovery user, because these cronjobs are added before the discovery user is created.
EDXAPP_ADDITIONAL_CRON_JOBS:
- name: "discovery: hourly course metadata refresh"
  user: "root"
  job: "sudo -u discovery bash -c 'source {{ discovery_home }}/discovery_env; {{ COMMON_BIN_DIR }}/manage.discovery refresh_course_metadata'"
  hour: "*"
  minute: "43"
  day: "*"
```

* Set these extra variables on the instance:

```yaml
# prevent creating example partners; this isn't required, and will cause provision errors later
ecommerce_create_demo_data: false

SANDBOX_ENABLE_DISCOVERY: yes
SANDBOX_ENABLE_ECOMMERCE: yes
DISCOVERY_VERSION: "{{ ECOMMERCE_VERSION }}"
COMMON_HOSTNAME: ""
ECOMMERCE_PAYMENT_PROCESSOR_CONFIG:
    partn_id: # this is arbitrary, limited to 8 characters; will be used later
      paypal:
        ...

# Have to build the full broker URLs to ensure the vhost path is included
ECOMMERCE_BROKER_URL: '{{ EDXAPP_CELERY_BROKER_TRANSPORT }}://{{ EDXAPP_CELERY_USER }}:{{ EDXAPP_CELERY_PASSWORD }}@{{ EDXAPP_CELERY_BROKER_HOSTNAME }}{{ EDXAPP_CELERY_BROKER_VHOST }}'
ECOMMERCE_WORKER_BROKER_URL: '{{ EDXAPP_CELERY_BROKER_TRANSPORT }}://{{ EDXAPP_CELERY_USER }}:{{ EDXAPP_CELERY_PASSWORD }}@{{ EDXAPP_CELERY_BROKER_HOSTNAME }}{{ EDXAPP_CELERY_BROKER_VHOST }}'
ECOMMERCE_WORKER_ECOMMERCE_API_ROOT: '{{ ECOMMERCE_ECOMMERCE_URL_ROOT }}/api/v2/'
```
* To change the default currency used in the ecommerce system from USD ($) to, for example, British pounds (£), add this extra configuration:

```yaml
# Use a configuration branch which contains this fix:
# https://github.com/open-craft/configuration/pull/119/files
EDXAPP_PAID_COURSE_REGISTRATION_CURRENCY: ['gbp', '£']
ECOMMERCE_OSCAR_DEFAULT_CURRENCY: 'GBP'
ECOMMERCE_REPOS:
  - PROTOCOL: '{{ COMMON_GIT_PROTOCOL }}'
    DOMAIN: '{{ COMMON_GIT_MIRROR }}'
    PATH: 'open-craft'
    REPO: 'ecommerce.git'
    # Use a branch which contains this fix:
    # https://github.com/open-craft/ecommerce/pull/13/files
    VERSION: opencraft-release/juniper.2
    DESTINATION: "{{ ecommerce_code_dir }}"
    SSH_KEY: '{{ ECOMMERCE_GIT_IDENTITY }}'

# Append to any existing EDXAPP_LMS_ENV_EXTRA:
EDXAPP_LMS_ENV_EXTRA:
  COURSE_MODE_DEFAULTS:
    bulk_sku: !!null
    currency: gbp
    description: !!null
    expiration_datetime: !!null
    min_price: 0
    name: Honor
    sku: !!null
    slug: honor
    suggested_prices: ''
```

**Notes**:

* We need to set the `COMMON_HOSTNAME` to something other than the external lms domain name (eg. `openlearning.example.com`), so that API requests made on the server can be properly routed through the
  load balancer-terminated SSL connection.  This is required because, by default, an /etc/hosts entry for the `COMMON_HOSTNAME` is set pointing to localhost, which will break SSL connections to the
  LMS from within the instance.
* The [`ECOMMERCE_PAYMENT_PROCESSOR_CONFIG`](https://github.com/edx/configuration/blob/open-release/juniper.2/playbooks/roles/ecommerce/defaults/main.yml#L103) should contain the payment processors
  and their keys.
* A larger appserver vm type may need to be used, since it will be running ecommerce and course discovery as well.

### Manual steps

Spawn a new appserver to use the updated settings to deploy the ecommerce and discovery services.

Once the appserver is running, you'll need to run the following commands on the new appserver to finish setup. These are
one-time actions that are stored in the database.

* In Django Admin > Authentication > Users (`/admin/auth/user/`), there should already be service users created, i.e. `ecommerce_worker` and `discovery_worker`.

    If not, create them with staff privileges, no password.

    Set a Full Name on `ecommerce_worker` and `discovery_worker`, so that a user profile is associated with the users.

    Add these extra permissions to the `ecommerce_worker`:

        api_admin | catalog | *
        bulk_email | course mode target | *
        commerce | commerce configuration | *
        course_modes | * | *

* In Django Admin > OAuth2 > Clients (`/admin/oauth2/client/`), there should already be clients created for ecommerce and discovery.

    If not, [create and register new clients](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html#configure-edx-openid-connect-oidc)
    for each service.  Attach each client to the worker user discussed in the previous step.

    You'll need the client IDs and client secrets for the next steps.

* In the ecommerce env, add a Site, Partner, and Site Configuration as per the instructions in the [edX ecommerce
  docs](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html#add-another-site-partner-and-site-configuration).

   * `--partner-code` should match the partner code from `ECOMMERCE_PAYMENT_PROCESSOR_CONFIG`, limited to 8 characters.
   * Add `--client-side-payment-processor stripe` if `ECOMMERCE_PAYMENT_PROCESSOR_CONFIG` uses the Stripe payment processor.

     See [payment processor docs](https://edx-ecommerce.readthedocs.io/en/latest/additional_features/payment_processors.html) for other arguments for specific payment processors.
   * `--from-email` should match `EDXAPP_DEFAULT_FROM_EMAIL`
   * Any of the values from the `create_or_update_site` command can be edited later in the ecommerce Django admin at `/admin/core/siteconfiguration/`; no need to continue rerunning this command once
     the initial auth related setup is working for the site configuration.

```bash
sudo -u ecommerce -Hs
cd
source ecommerce_env
source venvs/ecommerce/bin/activate
cd ecommerce
python manage.py create_or_update_site \
 --site-name 'My Site E-Commerce' \
 --site-domain 'ecommerce.lms.external.domain' \
 --partner-code 'partn_id' \
 --partner-name 'Partner Name' \
 --lms-url-root 'https://lms.external.domain' \
 --client-id '{ecommerce_worker oauth client id}' \
 --client-secret '{ecommerce_worker oauth client secret}' \
 --from-email 'user@example.com' \
 --discovery_api_url 'https://discovery.external.lms.domain/api/v1'
```

* In the discovery env, configure a partner using
  [`create_or_update_partner`](https://github.com/edx/course-discovery/blob/master/course_discovery/apps/core/management/commands/create_or_update_partner.py).

    * Use the same partner `--code` as what you used for ecommerce.

```bash
sudo -u discovery -Hs
cd
source discovery_env
source venvs/discovery/bin/activate
cd discovery
python manage.py create_or_update_partner \
  --site-id 1 \
  --site-domain 'discovery.external.lms.domain' \
  --code 'partn_id' \
  --name 'Client Name' \
  --courses-api-url 'https://external.lms.domain/api/courses/v1/' \
  --ecommerce-api-url 'https://ecommerce.external.lms.domain/api/v2/' \
  --organizations-api-url 'https://external.lms.domain/api/organizations/v0/' \
  --oidc-url-root 'https://external.lms.domain/oauth2' \
  --oidc-key '{discovery oauth client id}' \
  --oidc-secret '{discovery oauth client secret}'
```

* To initialize a new Elasticsearch index, run these commands on the appserver:

```bash
sudo -u discovery -Hs
source ~/discovery_env
/edx/bin/manage.discovery update_index --disable-change-limit
/edx/bin/manage.discovery refresh_course_metadata  # this task should be cron'd, see above.
```

* [Configure LMS to use ecommerce](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html#switch-from-shoppingcart-to-e-commerce)

### Test your configuration

1. Verify the OIDC login for both services:

        https://ecommerce.external.lms.domain/login
        https://discovery.external.lms.domain/login

1. Verify that the discovery cronjob runs without errors:

        sudo -u discovery -Hs
        source /edx/app/discovery/discovery_env
        /edx/bin/manage.discovery refresh_course_metadata

1. Publish a new course to test ecommerce.
1. Add a new [Course seat](https://edx-ecommerce.readthedocs.io/en/latest/create_products/create_course_seats.html) for this course, with a nominal charge (e.g. $1).
1. Optionally add a [Coupon](https://edx-ecommerce.readthedocs.io/en/latest/create_products/create_coupons.html) for the course, if the client will use coupons.
1. Enroll a new user into the test course, and verify that the coupon works, payments are processed, and the enrollment succeeds.
   Ideally, the payment processor will be initially configured as a sandbox service for testing, and so you can use test credit card numbers as provided by the payment processor.
1. Delete the course once all is verified.

## References

Useful references when configuring or troubleshooting issues with ecommerce and course discovery.

* [E-Commerce usage docs](https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/create_products/index.html)
* [Adding E-Commerce to the Open edX Platform](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html)
* [edX Discovery Service](http://edx-discovery.readthedocs.io/)
* [Setup Discovery Sandbox](https://openedx.atlassian.net/wiki/spaces/EDUCATOR/pages/162488548/Setup+Discovery+Sandbox)

## Mass Upgrades and Reconfigurations

To enable expedient upgrades across instances when there is a major update to the OpenEdX platform, the `instance_redeploy` management command is available.

The `instance_redeploy` command requires several options to know which servers to upgrade and how to update them. Note that major platform updates are not the 
only use for this command-- it can be used to fan out improvements to configuration as well.

The following arguments are available:

|     Name    |  Required?  | Description |
| ----------- | ----------- | ----------- |
|**--tag**| Yes | Base name of the tag used to mark instances for redeployment.  After the redeployment is complete, all instances which are successfully redeployed will be marked with this tag.  Instances which failed to redeploy will be marked with tag + `-failed`.  E.g., `zebrawood-redeployment-failed`. |
|**--filter**| No | If omitted, respawn **ALL** unarchived instances. This should point to a YAML file that contains a data structure that can be passed via `**kwargs` to `OpenEdXInstance.objects.filter`. For example, `{'ref_set__id__in': [200]}`. |
|**--exclude**| No | Like filter, but in reverse. This should point to a YAML file that contains a data structure that can be passed via `**kwargs` to `OpenEdXInstance.objects.exclude`. Useful if `--filter` might include instances that you need to make exceptions for. |
|**--update**| No | Specify a YAML file with fields to update on the `OpenEdxInstance` before spawning the new app servers. For instance, setting `edx_platform_commit` to the latest release tag name. Note that this will replace each key in those settings-- so for nested data structures where the current settings are important to preserve, you should update these configurations manually ahead of time. |
|**--preupgrade-sql-commands**| No | A list of SQL instructions to run, one after another, loaded from a YAML file that contains only an array. These will be run before the upgrade begins, and can be used to remediate any issues migrations are not able to solve on their own. **NOTE**: Failures from these commands will be silent. |
|**--force**| No | Don't prompt to confirm settings before beginning upgrades. Useful if this command is being used as part of a script, or if you are feeling particularly infallible today.|
|**--no-activate**| No | Don't mark successfully provisioned app servers as 'active' after upgrading, nor old servers as 'inactive'. |
|**--batch-size**| No | How many app servers to provision at once. Don't make this more than the number of workers available or provisioning will likely fail. Default: 2. |
|**--batch-frequency**| No | How frequently (in seconds) to check if workers are available to start the next app server upgrade. Default: 600 (10 minutes). |
|**--num-attempts**| No | How many times to attempt provisioning an app server before giving up. Default: 1|
|**--show-instances**| No | Don't actually redeploy-- show which instances would be provisioned and then exit.|

### Upgrade Walkthrough

Say you have a number of instances running the `ironwood.2` tagged release of `edx-platform` and you wish to upgrade them to `juniper.2`. The following files and commands would provide a plausible upgrade path. Move one directory up from your OCIM installation and create a directory for your configuration files. We'll name ours `upgrade`.

We first need a `.yml` file for the `--filter` argument to ensure we only grab instances that we intend to upgrade. Create a file named `filter.yml` with a check for the correct platform version:
```
---
edx_platform_commit: opencraft-release/ironwood.2
```

**NOTE**: In this demonstration, we are assuming the tags are pulled from [OpenCraft's fork of edx-platform](https://github.com/open-craft/edx-platform/). This fork is where we store modified releases with backported patches for OCIM.

If there are any special instances we know are on `opencraft-release/ironwood.2` that we do NOT want to upgrade, we will want to create an `exclude.yml` for these cases:

```
---
ref_set__id__in:
  # School of Hard Knox
  - 100
  # ACME Looniversity Gritty Reboot Devision
  - 45
```

From `ironwood.2` to `juniper.2` there is one dependency with a broken migration we need to remediate. We'll create a `sql.yml` file for this:

```
---
# Faking this migration due to https://stackoverflow.com/a/35143733/4302112
- "INSERT into django_migrations (app, name) values('thumbnail', '0001_initial');"
```

And, of course, we need an `update.yml` file containing the updated configuration settings for the new release.

```
---
openedx_release: open-release/juniper.2
edx_platform_repository_url: https://github.com/open-craft/edx-platform
edx_platform_commit: opencraft-release/juniper.2
configuration_source_repo_url: https://github.com/open-craft/configuration
configuration_version: opencraft-release/juniper.2
```

Finally, we can run the upgrades with:

```
HUEY_QUEUE_NAME=opencraft_low_priority honcho run python3 manage.py instance_redeploy \
   --batch-size=6 --num-attempts=3 \
   --tag=juniper2 \
   --filter=@../upgrade/filter.yml \
   --exclude=@../upgrade/exclude.yml \
   --update=@../upgrade/update.yml \
   --preupgrade-sql-commands=@../upgrade/sql.yml \
    |& tee -a @../upgrade/redeploy.log
```

Note the `HUEY_QUEUE_NAME` environment variable-- we set it here to use our alternative, low-priority queue so that we don't tie up workers dedicated to OCIM's normal customer-facing functions.
We also use the `juniper2` tag as a way to mark instances that have been updated as we go along (see the documentation on the `--tag` argument above.)

The command will give you a summary of what it intends to do, and then prompt you for confirmation. It is recommended you add 
the `--show-instances` argument to do a dry run and see the specific instances that will be upgraded. Any failures will be logged 
and tagged for further examination.