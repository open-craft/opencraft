"""
REST Framework API - Router
"""

# Imports #####################################################################

from rest_framework import routers

from instance.views import OpenStackServerViewSet, OpenEdXInstanceViewSet


# Router ######################################################################

router = routers.DefaultRouter()

router.register(r'openstackserver', OpenStackServerViewSet)
router.register(r'openedxinstance', OpenEdXInstanceViewSet)
