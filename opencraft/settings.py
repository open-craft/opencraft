"""
Django settings for opencraft project.

To configure your instance, use local_settings.py
See local_settings.sample
"""

import logging
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


ALLOWED_HOSTS = []


# Application definition

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
        'DIRS': [os.path.join(BASE_DIR, p, 'templates') for p in [''] + list(LOCAL_APPS)],
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


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # other finders..
    'compressor.finders.CompressorFinder',
)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

STATIC_ROOT = os.path.join(BASE_DIR, 'build/static')
STATIC_URL = '/static/'

# Always use IPython for shell_plus
SHELL_PLUS = "ipython"

# runserver_plus
RUNSERVERPLUS_SERVER_ADDRESS_PORT = '0.0.0.0:2000'

# Grappelli
GRAPPELLI_ADMIN_TITLE = 'OpenCraft'
GRAPPELLI_SWITCH_USER = True

# SASS
COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)

# REST framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissions',
    ],
}

# SwampDragon settings
SWAMP_DRAGON_CONNECTION = ('swampdragon.connections.sockjs_connection.DjangoSubscriberConnection', '/data')
DRAGON_URL = 'http://localhost:2001/'

# [Optional] Ansible worker queue #############

# Huey (redis task queue)
HUEY = {
    'backend': 'huey.backends.redis_backend',
    'name': 'opencraft',
    'connection': {'host': 'localhost', 'port': 6379},
    'always_eager': False, # Defaults to False when running via manage.py run_huey

    # Options to pass into the consumer when running ``manage.py run_huey``
    'consumer_options': {'workers': 4, 'loglevel': logging.INFO,},
}

# OpenStack
OPENSTACK_USER = None
OPENSTACK_PASSWORD = None
OPENSTACK_TENANT = None
OPENSTACK_AUTH_URL = None
OPENSTACK_REGION = None

OPENSTACK_SANDBOX_FLAVOR = {'ram': 4096, 'disk': 40}
OPENSTACK_SANDBOX_BASE_IMAGE = {'name': 'Ubuntu 12.04'}

# DNS (Gandi)
GANDI_API_KEY = None
GANDI_ZONE_ID = None

# GitHub - Forks & organizations
GITHUB_ACCESS_TOKEN = None
DEFAULT_FORK = 'edx/edx-platform'
WATCH_FORK = DEFAULT_FORK
WATCH_ORGANIZATION = None

# Logging #####################################################################

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
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'log/main.log',
            'formatter': 'verbose'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'propagate': True,
            'level':'DEBUG',
        },
        'django': {
            'handlers': ['file', 'console'],
            'propagate': False,
            'level':'INFO',
        },
        'opencraft': {
            'handlers': ['file', 'console'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'requests': {
            'handlers': ['file', 'console'],
            'propagate': False,
            'level': 'WARNING',
        }
    }
}
