"""
REST Framework API - Router
"""

# Imports #####################################################################

from rest_framework import routers

from task.views import ProjectViewSet, TaskViewSet
from user.views import OrganizationViewSet


# Router ######################################################################

router = routers.DefaultRouter()

router.register(r'organization', OrganizationViewSet)
router.register(r'project', ProjectViewSet)
router.register(r'task', TaskViewSet)
