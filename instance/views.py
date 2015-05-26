
# Imports #####################################################################

from rest_framework import viewsets

from .models import OpenStackServer, OpenEdXInstance
from .serializers import OpenStackServerSerializer, OpenEdXInstanceSerializer


# Views - API #################################################################

class OpenStackServerViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = OpenStackServer.objects.all()
    serializer_class = OpenStackServerSerializer

class OpenEdXInstanceViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = OpenEdXInstance.objects.all()
    serializer_class = OpenEdXInstanceSerializer
