Ansible playbook for the deployment of the OpenCraft Instance Manager
=====================================================================

The playbook in this directory can be used to deploy the OpenCraft Instance Manager to a server
running on Ubuntu 16.04 xenial.  It has been tested with this image:

https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img

You need two DNS names pointing to your server, one for the web server itself and another one for
web sockets.  The recommended setup is to add the subdomain "websocket" to the web server domain
name as the web socket domain.

The databases need to run on external servers.  The server deployed by this playbook is intended to
be stateless, and no backups are performed by default.

Running the playbook
--------------------

1. Create a file `private.yml` with your settings for the instance manager.  The settings go in the
   `OPENCRAFT_ENV_TOKENS` dictionary, e.g.

        OPENCRAFT_ENV_TOKENS:
          DATABASE_URL: 'postgres://db-user:password@postgres.example.com:port/db-name'
          DEFAULT_FORK: 'edx/edx-platform'
          SECRET_KEY: 'your-secret-key-goes-here'

   See the `README.md` file in the top-level directory and `opencraft/settings.py` for further details
   on settings you want to include there.

2. Install Ansible, e.g. by creating a new Python 2 virtualenv and running

        pip install -r requirements.txt

3. Install all required roles:

        ansible-galaxy install -r requirements.yml

4. Prepare your server with a stock Ubuntu 16.04 image, and make sure you can SSH to it.  Manually
   install Python 2 by running

        sudo apt-get update && sudo apt-get install -y python

   on the target server.  (Since Ansible requires Python 2 to be present on the target machine, we
   can't use Ansible to install Python 2.)

5. Run the playbook:

        ansible-playbook opencraft.yml -u ubuntu --extra-vars @private.yml -i your.host.name.here,

   (The trailing comma must be preserved.)

After deployment, the server doesn't run the instance manager automatically.  You need to log in
and run it manually inside a `screen` or `tmux` session:

1. SSH into your server.

2. Start `screen`.

3. Become the `www-data` user: `sudo -s -H -u www-data`

4. Run the server and workers: `/var/www/.virtualenvs/opencraft/bin/exec make run WORKERS=5`

5. Detach the `screen` session to log out again, leaving the server running.
