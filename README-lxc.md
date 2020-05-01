LXC installation
----------------

If you're running Linux on your workstation and would like to run the OCIM
development environment in a container, we suggest
[LXD](https://linuxcontainers.org/lxd/).  This will keep it isolated from the
rest of your system just like the Vagrant devstack, but with native performance
and added flexibility.

> Note: This method is not officially supported.  If you run into problems, we
> recommend that you follow one of the official installation methods [in the
> documentation](https://ocim.opencraft.com/en/latest/installation/) instead.

LXD is a wrapper over [LXC](https://linuxcontainers.org/lxc/) that makes
container management much simpler.  You will also use Ansible
[Ansible](https://www.ansible.com/) to provision your container.

The rest of this section assumes you're running a recent version of Ubuntu.

Start by opening a terminal and setting some useful environment variables.
`SRC` should point to the OCIM checkout, and `CONTAINER` is the desired LXC
container name.

    SRC=~/src/ocim
    CONTAINER=ocim

Check the necessary repositories out:

    mkdir -p $SRC
    cd $SRC
    git clone https://github.com/open-craft/opencraft ocim
    git clone https://github.com/open-craft/ansible-playbooks

Install LXD, and launch a Xenial container.

    sudo apt install lxd
    lxc launch ubuntu:16.04 $CONTAINER

Configure the container to mount the `SRC` directory automatically under
`/home/ubuntu`.  With this setup, any changes you make to the `$SRC` directory
locally will show up immediately in the container:

    lxc config device add $CONTAINER src disk source=$SRC path=/home/ubuntu/src

Also configure it to map the ubuntu user to your own user, so the former can
write to the mounted directory and the files within.  You must restart the
container afterwards:

    printf "uid $(id -u) 1000\ngid $(id -g) 1000" | lxc config set $CONTAINER raw.idmap -
    lxc restart $CONTAINER

To make it simple to SSH into the container, add your keys to the ubuntu user's
`authorized_keys`, and create a static host for its IP address.  Replace the
sample IP address given below with the one you find via `lxc info`.

    ssh-add -L | lxc exec $CONTAINER -- bash -c "cat >> /home/ubuntu/.ssh/authorized_keys"
    lxc info $CONTAINER | grep eth0
    echo "10.37.126.185 ocim.lxc" >> /etc/hosts

It is suggested that you configure SSH to always use the "ubuntu" user when
connecting to LXC containers, and to forward the X11 API by default.  This
makes the connection process even simpler.  Edit `~/.ssh/config` using your
favorite editor, and insert the following stanza at the end of the file:

    # Containers
    Host *.lxc
        User ubuntu
        ForwardX11 yes
        StrictHostKeyChecking no

You can now connect to the container via:

    ssh ocim.lxc

In the container, install the supported ansible version into a Python3 venv and
activate it.  You must install some additional dependencies manually:

    sudo apt install python3-venv python3-dev libffi-dev
    mkdir ~/venvs
    python3 -m venv ~/venvs/ansible
    . ~/venvs/ansible/bin/activate
    cd ~/src/ansible-playbooks
    pip install wheel
    pip install pip==9.0.3
    pip install -r requirements.txt

Run the `ocim-devstack` playbook locally, and deactivate the ansible venv after
a successful run.

    ansible-playbook -c local -i 127.0.0.1, playbooks/ocim-devstack.yml
    deactivate

This will have provisioned the container with Postgres, MySQL, MongoDB and
Redis, and installed system dependencies.

Now, disconnect from the container, and ssh back in.  A `pyenv` environment
should be activated, and the current directory should be set to the source
checkout.   Proceed by installing the project Python dependencies:

    pip install -r requirements.txt

Then run migrations, so the database is updated:

    make migrate

Now, create a superuser account which will be used to log in to Ocim.  Make
sure to save the details for later.

    make manage createsuperuser

At this point, create a `.env` file if it doesn't already exist, and set the
following environment variables in it:

    ALLOWED_HOSTS='["ocim.lxc"]'
    HUEY_ALWAYS_EAGER=false

Finally, you're ready to run the development server:

    make run.dev

You can access the main page at http://ocim.lxc:5000/ using any browser.  Log
in with the superuser credentials you created above.
