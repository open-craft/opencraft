FROM ubuntu:xenial
ARG USER_NAME
ENV USER_NAME ${USER_NAME:-root}
ARG USER_ID
ENV USER_ID ${USER_ID:-0}

#### Docker specific ###########################################################
#
# en_US.UTF-8 is assumed to always be installed
#
RUN apt-get update && apt-get install -y locales && locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
#
# Install dependencies
#
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y sudo ca-certificates openssh-server
#
# All commands are run via exec under a non privileged user that has the same name as the user building the image
# and the same id. So that volumes mounted from a directory they own are not unexpectedly chowned to root in various
# places.
#
RUN if test $USER_NAME != root ; then useradd --no-create-home --home-dir /tmp --uid $USER_ID $USER_NAME && echo "$USER_NAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers ; fi
#
#### Install dependencies ######################################################
#
# Firefox 52 for selenium compatibility
#
RUN apt-get install -y software-properties-common && add-apt-repository --yes ppa:jonathonf/firefox-esr-52 && apt-get update && apt-get install -y firefox-esr
#
# Install postgresql 10 because ansible-playbooks/playbooks/group_vars/postgres/public.yml
# has version 10 and ansible-playbooks/playbooks/roles/postgres/tasks/main.yml installs it
# 
RUN echo 'deb http://apt.postgresql.org/pub/repos/apt/ xenial-pgdg main' >> /etc/apt/sources.list.d/pgdg.list && wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y postgresql-10
#
# Install consul
#
RUN apt-get install -y unzip && wget -P /tmp https://releases.hashicorp.com/consul/1.2.1/consul_1.2.1_linux_amd64.zip && unzip /tmp/consul_1.2.1_linux_amd64.zip -d /usr/local/bin
COPY devstack/consul.service /etc/systemd/system/consul.service
RUN systemctl enable consul
#
# Install system & databases dependencies
#
WORKDIR /opt
COPY Makefile .
COPY debian_packages.lst .
COPY debian_db_packages.lst .
RUN apt-get update && apt-get install -y make && DEBIAN_FRONTEND=noninteractive make install_system_db_dependencies install_system_dependencies
#
# Setup a virtual environment owned by the user with all python dependencies installed
#
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv
COPY requirements.txt .
COPY cleanup_utils/requirements.txt cleanup_utils/requirements.txt
RUN python3 -m venv venv && . venv/bin/activate && pip install --upgrade pip && pip install --upgrade virtualenv && pip install -r requirements.txt && pip install -r cleanup_utils/requirements.txt && chown -R $USER_NAME venv
#
#### Prepare the development environment #######################################
#
# The user should be allowed to tamper with the installed virtualenv for debugging purposes
#
RUN chown -R ${USER_NAME} /opt
#
# Install a one shot script to be run when systemd is finished spawning services
# and carry out all actions that cannot be run when building the dockerfile, such
# as creating a database user to allow access to the non-privileged user.
#
COPY devstack/setup-devstack.sh /usr/local/bin/setup-devstack.sh
RUN sed -i -e "s/%%USER_NAME%%/$USER_NAME/g" \
           -e "s/%%USER_ID%%/$USER_ID/g" \
	   /usr/local/bin/setup-devstack.sh
COPY devstack/setup-devstack.service /etc/systemd/system/setup-devstack.service
RUN systemctl enable setup-devstack
#
# Setup run whenever the user runs exec (there is no way to run .bashrc etc. when entering a container)
#
COPY devstack/shell.sh /usr/local/bin/shell.sh
#
# This is 100% duplicated from .env.test although only a few values needs replacement, it should be split
#
ENV HONCHO_TEST_ENV=devstack/honcho.env.test.tmp
ENV HONCHO_ENV=devstack/honcho.env.tmp
