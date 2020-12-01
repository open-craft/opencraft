Using the Ocim web console
--------------------------

This section focuses on how to use the web interface, as opposed to how to install, debug or develop Ocim;
see the following sections for that.

![Ocim's main screen](images/ocim_main_screen.png)

At the left there's a list of instances, and each instance has many appservers.
We can create a new appserver through the **Launch new AppServer** button;
it will automatically get the current configuration from the instance settings
and use it for this server.
After 1 to 2 hours, it will finish and then you need to **activate** the new one
and **deactivate** the old one, to make the load balancer update its configuration
so that the domain name of the instance directs to the new one.
Normally we want just 1 active appserver per instance, but two or more active at once
may be required in some high-resource-utilization cases.
Before activating a server, there's the option to test it through a
basic-auth password-protected link in the "Authenticated Link" section
(the username and password are embedded in the link).
If you want to terminate a VM associated with an App Server, first you must
**deactivate** it and then **terminate**. Notice that only instances with an
associated pull request can have all its App Servers deactivates/terminated.

Sometimes Open edX playbook fails, and then you need to read the log,
which is shown in real-time in the web console.
You can fix the settings and then spawn another server.
Failed and old inactive servers are automatically cleaned up after some configurable amount of days.
An important feature is that Ocim *grants SSH access* to members of a configurable GitHub organization,
so you can always SSH to an appserver's IP, *even if Open edX's deployment failed*, and then debug it.
You can use your GitHub username and key.

To create a new instance, you use Django's admin and you need to fill in the domain name,
the prefixed domain names (for Studio, e-commerce, etc.), the edx-platform/configuration branches to use,
and extra ansible variables to pass to Open edX's playbook (if any).
OCIM generates server hostnames from the domain name, [truncating it to a fixed-length](https://github.com/open-craft/opencraft/blob/8e84edf8621d76a7a379bb62bd3dd726b83fbd6e/instance/models/openedx_appserver.py#L543). This might cause unforseen issues if multiple instances share a sufficiently long prefix, due to duplicate hostnames. See [SE-3484](https://tasks.opencraft.com/browse/SE-3484) as an example of such an issue.
The instance settings are used for new deployments only
(changing the instance settings doesn't retroactively redeploy appservers).
