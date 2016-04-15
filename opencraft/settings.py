# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015 OpenCraft <xavier@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Django settings for opencraft project.

To configure your instance, set the configuration variables,
using the variable name passed to `env()` below
"""

# Imports #####################################################################

import environ
import logging
import os

from urllib.parse import urlparse


# Functions ###################################################################

env = environ.Env()
root = environ.Path(os.path.dirname(__file__), os.pardir)


# Security ####################################################################

# Keep the secret key used in production secret
SECRET_KEY = env('SECRET_KEY')

ALLOWED_HOSTS = env.json('ALLOWED_HOSTS', default='[]')

DEBUG = env.bool('DEBUG', default=False)

LOGIN_URL = '/admin/login/'

# Database ####################################################################

# Set via the environment variable `DATABASE_URL`
DATABASES = {
    'default': env.db(),
}


# Application definition ######################################################

LOCAL_APPS = (
    'api',
    'instance',
)

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'foundation',
    'compressor',
    'djangular',
    'rest_framework',
    'huey.djhuey',
    'swampdragon',
    'debug_toolbar',
) + LOCAL_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'opencraft.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [root(p, 'templates') for p in [''] + list(LOCAL_APPS)],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.core.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'opencraft.wsgi.application'


# Internationalization ########################################################

# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images) ######################################

# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

STATICFILES_DIRS = (
    root('static'),
)

STATIC_ROOT = root('build/static')
STATIC_URL = '/static/'

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)


# Test runner #################################################################

TEST_RUNNER = env('TEST_RUNNER', default='django.test.runner.DiscoverRunner')


# Django-extensions ###########################################################

SHELL_PLUS = "ipython"
RUNSERVERPLUS_SERVER_ADDRESS_PORT = env('RUNDEV_SERVER_ADDRESS_PORT', default='0.0.0.0:5000')


# Grappelli ###################################################################

GRAPPELLI_ADMIN_TITLE = 'OpenCraft'
GRAPPELLI_SWITCH_USER = True


# REST framework ##############################################################

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions',
    ],
}


# Redis cache & locking #######################################################

REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/')
REDIS_URL_OBJ = urlparse(REDIS_URL)

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


# Huey (redis task queue) #####################################################

HUEY = {
    'backend': 'huey.backends.redis_backend',
    'name': 'opencraft',
    'connection': {
        'host': REDIS_URL_OBJ.hostname,
        'port': REDIS_URL_OBJ.port,
        'password': REDIS_URL_OBJ.password,
    },
    'always_eager': env.bool('HUEY_ALWAYS_EAGER', default=False),

    # Options to pass into the consumer when running ``manage.py run_huey``
    'consumer_options': {'workers': 1, 'loglevel': logging.DEBUG},
}


# SwampDragon (websocket) #####################################################

SWAMP_DRAGON_REDIS_HOST = REDIS_URL_OBJ.hostname
SWAMP_DRAGON_REDIS_PORT = REDIS_URL_OBJ.port
SWAMP_DRAGON_CONNECTION = ('swampdragon.connections.sockjs_connection.DjangoSubscriberConnection', '/data')
DRAGON_SERVER_ADDRESS_PORT = env('DRAGON_SERVER_ADDRESS_PORT', default='0.0.0.0:2001')
DRAGON_URL = env('DRAGON_URL', default='http://localhost:2001/')


# OpenStack ###################################################################

OPENSTACK_USER = env('OPENSTACK_USER')
OPENSTACK_PASSWORD = env('OPENSTACK_PASSWORD')
OPENSTACK_TENANT = env('OPENSTACK_TENANT')
OPENSTACK_AUTH_URL = env('OPENSTACK_AUTH_URL')
OPENSTACK_REGION = env('OPENSTACK_REGION')

OPENSTACK_SANDBOX_FLAVOR = env.json('OPENSTACK_SANDBOX_FLAVOR', default={"ram": 4096, "disk": 40})
OPENSTACK_SANDBOX_BASE_IMAGE = env.json('OPENSTACK_SANDBOX_BASE_IMAGE', default={"name": "Ubuntu 12.04"})
OPENSTACK_SANDBOX_SSH_KEYNAME = env('OPENSTACK_SANDBOX_SSH_KEYNAME', default='opencraft')
OPENSTACK_SANDBOX_SSH_USERNAME = env('OPENSTACK_SANDBOX_SSH_USERNAME', default='ubuntu')

# Separate credentials for Swift.  These credentials are currently passed on to each instance
# when Swift is enabled and INSTANCE_EPHEMERAL_DATABASES is disabled.

SWIFT_ENABLE = env.bool('SWIFT_ENABLE', default=True)
SWIFT_OPENSTACK_USER = env('SWIFT_OPENSTACK_USER', default=OPENSTACK_USER)
SWIFT_OPENSTACK_PASSWORD = env('SWIFT_OPENSTACK_PASSWORD', default=OPENSTACK_PASSWORD)
SWIFT_OPENSTACK_TENANT = env('SWIFT_OPENSTACK_TENANT', default=OPENSTACK_TENANT)
SWIFT_OPENSTACK_AUTH_URL = env('SWIFT_OPENSTACK_AUTH_URL', default=OPENSTACK_AUTH_URL)
SWIFT_OPENSTACK_REGION = env('SWIFT_OPENSTACK_REGION', default=OPENSTACK_REGION)


# DNS (Gandi) #################################################################

# Instances will be created as subdomains of this domain
INSTANCES_BASE_DOMAIN = env('INSTANCES_BASE_DOMAIN')

# The zone attached to the `INSTANCES_BASE_DOMAIN` in Gandi
# Get it from the URL when editing the domain zone
# 1) Login on your domain at Gandi
# 2) Go to -> Services > Domains > [yourdomain].com > Zone files > Edit the zone
# 3) Get id from URL, eg. 00000000 for https://www.gandi.net/admin/domain/zone/00000000/2/edit?fromDomain=3889
# Needs to be an integer, not a string.
GANDI_ZONE_ID = env.int('GANDI_ZONE_ID')

# See https://www.gandi.net/admin/api_key
GANDI_API_KEY = env('GANDI_API_KEY')


# GitHub - Forks & organizations ##############################################

# The worker queue will watch for PRs from members of a given organization
# and automatically spinup new instances when new commits are pushed to the PRs

# Get it from https://github.com/settings/tokens
GITHUB_ACCESS_TOKEN = env('GITHUB_ACCESS_TOKEN')

# Default github repository to pull code from
DEFAULT_FORK = env('DEFAULT_FORK', default='edx/edx-platform')

# Github fork to watch
WATCH_FORK = env('WATCH_FORK', default=DEFAULT_FORK)

# Github organization to watch
WATCH_ORGANIZATION = env('WATCH_ORGANIZATION')

# Default admin organization for instances (gets shell access)
DEFAULT_ADMIN_ORGANIZATION = env('DEFAULT_ADMIN_ORGANIZATION', default='')

# Fork and branch of the Open edX configuration repo used for sandboxes created for PRs.
DEFAULT_CONFIGURATION_REPO_URL = env(
    'DEFAULT_CONFIGURATION_REPO_URL', default='https://github.com/edx/configuration.git'
)
DEFAULT_CONFIGURATION_VERSION = env('DEFAULT_CONFIGURATION_VERSION', default='master')

# Ansible #####################################################################

# Ansible requires a Python 2 interpreter
ANSIBLE_PYTHON_PATH = env('ANSIBLE_PYTHON_PATH', default='/usr/bin/python')

# Time in seconds to wait for the next log line when running an Ansible playbook.
ANSIBLE_LINE_TIMEOUT = env.int('ANSIBLE_LINE_TIMEOUT', default=1500)  # 25 minutes

# Timeout in seconds for an entire Ansible playbook.
ANSIBLE_GLOBAL_TIMEOUT = env.int('ANSIBLE_GLOBAL_TIMEOUT', default=9000)  # 2.5 hours

# Emails ######################################################################

# From & subject configuration for sent emails
SERVER_EMAIL = env('SERVER_EMAIL', default='opencraft@locahost')
EMAIL_SUBJECT_PREFIX = env('EMAIL_SUBJECT_PREFIX', default='[OpenCraft] ')

# SMTP configuration
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env('EMAIL_PORT', default=25)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')


# Logging #####################################################################

ADMINS = env.json('ADMINS', default=set())

BASE_HANDLERS = env.json('BASE_HANDLERS', default=["file", "console"])
HANDLERS = BASE_HANDLERS + ['db']
LOGGING_ROTATE_MAX_KBYTES = env.json('LOGGING_ROTATE_MAX_KBYTES', default=10 * 1024)
LOGGING_ROTATE_MAX_FILES = env.json('LOGGING_ROTATE_MAX_FILES', default=60)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "{asctime} | {levelname:>8.8s} | process={process:<5d} | {name:<25.25s} | {message}",
            'style': '{',
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'db': {
            'format': "{name:<25.25s} | {message}",
            'style': '{',
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'db': {
            'level': 'INFO',
            'class': 'instance.logging.DBHandler',
            'formatter': 'db'
        },
    },
    'loggers': {
        '': {
            'handlers': HANDLERS,
            'propagate': True,
            'level': 'DEBUG',
        },
        'django': {
            'handlers': HANDLERS,
            'propagate': False,
            'level': 'INFO',
        },
        'opencraft': {
            'handlers': HANDLERS,
            'propagate': False,
            'level': 'DEBUG',
        },
        'requests': {
            'handlers': HANDLERS,
            'propagate': False,
            'level': 'DEBUG',
        }
    }
}

if 'file' in HANDLERS:
    LOGGING['handlers']['file'] = {
        'level': 'DEBUG',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': 'log/main.log',
        'maxBytes': LOGGING_ROTATE_MAX_KBYTES * 1024,
        'backupCount': LOGGING_ROTATE_MAX_FILES,
        'formatter': 'verbose'
    }


# Instances ###################################################################

# By default, instances use local mysql and mongo databases and local file storage.
# Set this to False to use external databases and Swift object storage instead.
INSTANCE_EPHEMERAL_DATABASES = env.bool('INSTANCE_EPHEMERAL_DATABASES', default=True)

# Configure external databases here
INSTANCE_MYSQL_URL = env('INSTANCE_MYSQL_URL', default=None)
INSTANCE_MONGO_URL = env('INSTANCE_MONGO_URL', default=None)
INSTANCE_MYSQL_URL_OBJ = urlparse(INSTANCE_MYSQL_URL) if INSTANCE_MYSQL_URL else None
INSTANCE_MONGO_URL_OBJ = urlparse(INSTANCE_MONGO_URL) if INSTANCE_MONGO_URL else None

# Limit the number of log entries fetched for each instance, for performance
LOG_LIMIT = env.int('LOG_LIMIT', default=10000)
