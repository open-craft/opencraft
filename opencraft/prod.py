"""
Production environment settings
"""

from opencraft.settings import * #pylint: disable=wildcard-import,unused-wildcard-import

# TODO: https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

DEBUG = False

try:
    from opencraft.local_settings import * #pylint: disable=wildcard-import,unused-wildcard-import
except ImportError:
    pass
