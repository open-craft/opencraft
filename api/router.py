"""
REST Framework API - Router
"""

# Imports #####################################################################

from rest_framework import routers

from instance.views import OpenStackServerViewSet, OpenEdXInstanceViewSet
from task.views import ProjectViewSet, TaskViewSet
from user.views import OrganizationViewSet


# Router ######################################################################

router = routers.DefaultRouter()

router.register(r'openstackserver', OpenStackServerViewSet)
router.register(r'openedxinstance', OpenEdXInstanceViewSet)
router.register(r'organization', OrganizationViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'task', TaskViewSet)
