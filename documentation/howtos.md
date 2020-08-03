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
    VERSION: opencraft-release/ironwood.2
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
* The [`ECOMMERCE_PAYMENT_PROCESSOR_CONFIG`](https://github.com/edx/configuration/blob/open-release/ironwood.2/playbooks/roles/ecommerce/defaults/main.yml#L103) should contain the payment processors
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
