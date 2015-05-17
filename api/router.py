"""
REST Framework API - Router
"""

# Imports #####################################################################

from rest_framework import routers

from task.views import TaskViewSet


# Router ######################################################################

router = routers.DefaultRouter()
router.register(r'task', TaskViewSet)
