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


# Django-extensions ###########################################################

SHELL_PLUS = "ipython"
RUNSERVERPLUS_SERVER_ADDRESS_PORT = '127.0.0.1:5000'


# Grappelli ###################################################################

GRAPPELLI_ADMIN_TITLE = 'OpenCraft'
GRAPPELLI_SWITCH_USER = True


# REST framework ##############################################################

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions',
    ],
}

# Huey (redis task queue) #####################################################

REDISTOGO_URL = env('REDISTOGO_URL', default='redis://localhost:6379/')
REDIS_URL = env('REDIS_URL', default=REDISTOGO_URL)
REDIS_URL_OBJ = urlparse(REDIS_URL)

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
    'consumer_options': {'workers': 4, 'loglevel': logging.DEBUG,},
}


# SwampDragon (websocket) #####################################################

SWAMP_DRAGON_REDIS_HOST = REDIS_URL_OBJ.hostname
SWAMP_DRAGON_REDIS_PORT = REDIS_URL_OBJ.port
SWAMP_DRAGON_REDIS_PASS = REDIS_URL_OBJ.password
SWAMP_DRAGON_CONNECTION = ('swampdragon.connections.sockjs_connection.DjangoSubscriberConnection', '/data')
DRAGON_URL = env('DRAGON_URL', default='http://localhost:2001/')


# OpenStack ###################################################################

OPENSTACK_USER = env('OPENSTACK_USER')
OPENSTACK_PASSWORD = env('OPENSTACK_PASSWORD')
OPENSTACK_TENANT = env('OPENSTACK_TENANT')
OPENSTACK_AUTH_URL = env('OPENSTACK_AUTH_URL')
OPENSTACK_REGION = env('OPENSTACK_REGION')

OPENSTACK_SANDBOX_FLAVOR = env.json('OPENSTACK_SANDBOX_FLAVOR', default='{"ram": 4096, "disk": 40}')
OPENSTACK_SANDBOX_BASE_IMAGE = env.json('OPENSTACK_SANDBOX_BASE_IMAGE', default='{"name": "Ubuntu 12.04"}')
OPENSTACK_SANDBOX_SSH_KEYNAME = env('OPENSTACK_SANDBOX_SSH_KEYNAME', default='opencraft')
OPENSTACK_SANDBOX_SSH_USERNAME = env('OPENSTACK_SANDBOX_SSH_USERNAME', default='ubuntu')


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


# Ansible #####################################################################

# Ansible requires a Python 2 interpreter
ANSIBLE_PYTHON_PATH = env('ANSIBLE_PYTHON_PATH', default='/usr/bin/python')


# Logging #####################################################################

ADMINS = env.json('ADMINS', default=set())

BASE_HANDLERS = env.json('BASE_HANDLERS', default=["file", "console"])
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': BASE_HANDLERS,
            'propagate': True,
            'level':'DEBUG',
        },
        'django': {
            'handlers': BASE_HANDLERS,
            'propagate': False,
            'level':'INFO',
        },
        'opencraft': {
            'handlers': BASE_HANDLERS,
            'propagate': False,
            'level': 'DEBUG',
        },
        'requests': {
            'handlers': BASE_HANDLERS,
            'propagate': False,
            'level': 'WARNING',
        }
    }
}

if 'file' in BASE_HANDLERS:
    LOGGING['handlers']['file'] = {
        'level': 'DEBUG',
        'class': 'logging.FileHandler',
        'filename': 'log/main.log',
        'formatter': 'verbose'
    }
