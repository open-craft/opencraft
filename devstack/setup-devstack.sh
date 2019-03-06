#!/bin/bash

set -xe

USER_NAME=%%USER_NAME%%

sudo -u postgres createuser -d ${USER_NAME}
sudo -u ${USER_NAME} createdb --encoding utf-8 --template template0 opencraft
