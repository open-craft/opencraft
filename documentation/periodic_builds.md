Periodic Builds
--------------------------

Ocim includes a tool to automatically spawn and provision new AppServers at
time intervals. The main use case for this is an adhoc continuous integration
service. The Open edX platform spans many dependencies, so rebuilding on new
commits to a repository isn't enough to catch possibly breaking changes
elsewhere in the dependency chain.

## Configuration

The behaviour of periodic builds can be configured for each instance from
the Django admin. The settings are:

---

- name: `periodic_builds_enabled`
- default: `False`

This is a boolean option that toggles whether this instance will have periodic
builds enabled. If disabled, no AppServers will be spawned automatically by the
periodic builds scheduler. If enabled, new AppServers will be spawned and
provisioned according to the following options.

---

- name: `periodic_builds_interval`
- default: `1 00:00:00` (1 day)

This is the time interval to wait between spawning each AppServer. For example,
if setting to 12 hours, a new AppServer will be spawned every 12 hours. It can
be formatted as "DD HH:MM:SS.uuuuuu" or as specified by ISO 8601 (e.g.
P4DT1H15M20S which is equivalent to 4 1:15:20) or PostgreSQL’s day-time
interval format (e.g. 3 days 04:05:06). For convenience, in the Django ORM, it
normalizes to a `timedelta`.

If an AppServer is manually spawned, the periodic builds scheduler will wait
for this interval before spawning a new AppServer. This is to avoid too many
Appservers from being spawned close together.

It is recommended to avoid setting this to short interval (less than 3 hours),
otherwise many AppServers will end up building simultaneously, causing a waste
of resources.

---

- name: `periodic_builds_retries`
- default: `0`

This is the number of times to retry spawning and provisioning an AppServer
on failure. Default is to not retry at all.


## Notification on failure

To be effective as a CI, this also needs to alert on failure.
The `provisioning_failure_notification_emails` setting allows entering a
comma-separated list of email addresses to notify if provisioning an AppServer
fails.

Note that this applies to all instances, not just those with periodic builds
enabled. It can be a useful option for development to receive an alert if an
AppServer fails to provision.

Example: `urgent+ci@example.com,me@example.com`
