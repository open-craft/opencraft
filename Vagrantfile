# -*- mode: ruby -*-
# vi: set ft=ruby :

# This script provisions a vagrant development environment with local
# postgres and redis servers for development and testing.
PROVISION = <<SCRIPT
set -e

# cd to /vagrant on login
cd /vagrant
grep -Fq 'cd /vagrant' ~/.bashrc || echo 'cd /vagrant' >> ~/.bashrc

# Install system packages
sudo apt-get update --quiet
sudo apt-get install -y $(cat debian_packages.lst) postgresql

# Set up a virtualenv
sudo pip3 install virtualenv
mkdir -p ~/.virtualenvs
virtualenv -p python3 ~/.virtualenvs/opencraft
source ~/.virtualenvs/opencraft/bin/activate

# Activate virtualenv on login
grep -Fq 'source ~/.virtualenvs/opencraft/bin/activate' ~/.bashrc ||
  echo 'source ~/.virtualenvs/opencraft/bin/activate' >> ~/.bashrc

# Install python dependencies
pip install -r requirements.txt

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
  config.vm.network 'forwarded_port', guest: 8888, host: 8888
  config.ssh.forward_x11 = true
  config.vm.provision 'shell',
                      inline: PROVISION,
                      privileged: false,
                      keep_color: true

  config.vm.provider :virtualbox do |vb|
    # Allow DNS to work for Ubuntu host
    # http://askubuntu.com/questions/238040/how-do-i-fix-name-service-for-vagrant-client
    vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end
end
