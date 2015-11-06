#!/bin/bash

set -e

# cd to /vagrant on login
cd /vagrant
grep -Fq 'cd /vagrant' ~/.bashrc || echo 'cd /vagrant' >> ~/.bashrc

# Install system packages
make apt_get_dist_upgrade install_system_dependencies install_system_db_dependencies

# Set up the python virtualenv & dependencies
make install_virtualenv_system
source ~/.bashrc
make install_python_dependencies

# Activate the virtualenv on login
grep -Fq 'source ~/.virtualenvs/opencraft/bin/activate' ~/.bashrc || \
    echo 'source ~/.virtualenvs/opencraft/bin/activate' >> ~/.bashrc

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
