
# Imports #####################################################################

from rest_framework import viewsets

from .models import Organization
from .serializers import OrganizationSerializer


# Views - API #################################################################

class OrganizationViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
