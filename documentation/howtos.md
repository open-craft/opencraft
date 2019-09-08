### Configuring ecommerce and Course Discovery

By default, instances are not provisioned with either ecommerce or the Course Discovery
service. However, support is available to manually enable those services. To do so:

* Ensure that the [`refresh_course_metadata` cron task](https://github.com/open-craft/configuration/blob/c1e576eabefea82d21d7785810126e39752cd14e/playbooks/roles/discovery/tasks/main.yml)
  is added to the ansible discovery tasks.
* Set these extra variables on the instance:

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

**Notes**:

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

        sudo -s -c . /edx/app/discovery/discovery_env; /edx/bin/manage.discovery refresh_course_metadata

Useful references:

* [Adding E-Commerce to the Open edX Platform](http://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/ecommerce/install_ecommerce.html)
* [edX Discovery Service](http://edx-discovery.readthedocs.io/)
* [Setup Discovery Sandbox](https://openedx.atlassian.net/wiki/spaces/EDUCATOR/pages/162488548/Setup+Discovery+Sandbox)
