# -*- mode: ruby -*-
# vi: set ft=ruby :

# This script provisions a vagrant development environment with local
# postgres and redis servers for development and testing.
PROVISION = <<SCRIPT
set -e

# cd to /vagrant on login
cd /vagrant
grep -q 'cd /vagrant' ~/.bashrc || echo 'cd /vagrant' >> ~/.bashrc

# Install system packages
sudo apt-get update --quiet
sudo apt-get install -y $(cat debian_packages.lst) postgresql

# Upgrade pip
sudo pip3 install --upgrade pip

# By default, pip will install editable packages in ./src/ which is inside
# the virtualbox share. This can slow things like prospector down a lot, so
# configure pip to install them at the usual dist-packages location instead.
cat << EOF | sudo tee /etc/pip.conf
[install]
src = /usr/local/lib/python3.4/dist-packages
EOF

# Install python dependencies
sudo pip install -r requirements.txt

# Create postgres user
sudo -u postgres createuser -d vagrant

# Allow access to postgres from localhost without password
cat << EOF | sudo tee /etc/postgresql/9.3/main/pg_hba.conf
local   all             postgres                                peer
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
EOF
sudo service postgresql restart

# Create postgres database
createdb --encoding utf-8 --template template0 opencraft

# Use test configuration for local development, excluding the line that
# disables logging to the console.
[ -e .env ] || grep -v '^BASE_HANDLERS' .env.test > .env

# Run unit tests
make test_unit
SCRIPT

Vagrant.configure(2) do |config|
  config.vm.box = 'ubuntu/trusty64'
  config.vm.network 'forwarded_port', guest: 2001, host: 2001
  config.vm.network 'forwarded_port', guest: 5000, host: 5000
  config.vm.provision 'shell',
                      inline: PROVISION,
                      privileged: false,
                      keep_color: true
end
