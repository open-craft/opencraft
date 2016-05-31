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

Prepare configuration file
--------------------------

Create a file `private.yml` with your settings for the instance manager.  Most of the settings go in the
`OPENCRAFT_ENV_TOKENS` dictionary, e.g.

    OPENCRAFT_ENV_TOKENS:
      DATABASE_URL: 'postgres://db-user:password@postgres.example.com:port/db-name'
      DEFAULT_FORK: 'edx/edx-platform'
      SECRET_KEY: 'your-secret-key-goes-here'

Set `OPENCRAFT_OPENSTACK_SSH_KEY_FILE` to the name of the private SSH key to be used to access
OpenStack servers.  You must upload the corresponding public key to the OpenStack project
configured in OPENCRAFT_ENV_TOKENS and set OPENSTACK_SANDBOX_SSH_KEYNAME to the name of the key.

See the `README.md` file in the top-level directory and `opencraft/settings.py` for further details
on settings you want to include there.

### Deployment of swift backup
 
Optionally Instance Manager allows you to set up SWIFT container for spawned edx instances (bear in mind that 
support for swift containers hasn't been merged to master by the time of writing that). More optionally yet 
this swift containers may be backed up to tarsnap service.  To do this you'll need to set all variables starting 
from: `OPENCRAFT_BACKUP_SWIFT_*`. 

Swift backup downloads all swift containers, to local drive (this is the only way to back them up to Tarsnap), these 
containers might take a lot of space --- so it might be good idea to mount download them to a separate filesystem. 

To do this you'll need to:
 
1. Create a OpenStack Volume. 
2. Partition it (create a single partition --- use `fdisk`)
3. Create ext4 filesystem on it `mkfs.ext4 -j`.
4. Set `OPENCRAFT_BACKUP_SWIFT_MOUNT_DEVICE` to point to this device. 

Run the playbook
----------------


1. Install Ansible, e.g. by creating a new Python 2 virtualenv and running

        pip install -r requirements.txt

2. Install all required roles:

        ansible-galaxy install -r requirements.yml

3. Prepare your server with a stock Ubuntu 16.04 image, and make sure you can SSH to it.

4. Run the playbook:

        ansible-playbook opencraft.yml -u ubuntu --extra-vars @private.yml -i your.host.name.here,

   (The trailing comma must be preserved.). Note: you can't pass naked ip address to -i switch, long 
   story short this will make `forward-server-mail` explode when configuring postfix. Please temporarily
   add hostname mapping to your hosts if you need to, or just create an ansible ``hosts`` file.  

After deployment, the server doesn't run the instance manager automatically.  You need to log in
and run it manually inside a `screen` or `tmux` session:

1. SSH into your server.

2. Start `screen`.

3. Become the `www-data` user with `sudo -s -H -u www-data` and cd to `/var/www/opencraft`.

4. Run the server and workers: `/var/www/.virtualenvs/opencraft/bin/exec make run WORKERS=5`

5. Detach the `screen` session to log out again, leaving the server running.
