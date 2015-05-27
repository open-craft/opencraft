
# Imports #####################################################################

from django.shortcuts import render
from rest_framework import viewsets

from .models import OpenStackServer, OpenEdXInstance
from .serializers import OpenStackServerSerializer, OpenEdXInstanceSerializer


# Functions - Helpers #########################################################

def get_context():
    instance_list = OpenEdXInstance.objects.order_by('-created')

    context = {
        'instance_list': instance_list,
    }

    return context


# Views #######################################################################

def index(request):
    return render(request, 'instance/index.html', get_context())


# Views - API #################################################################

class OpenStackServerViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = OpenStackServer.objects.all()
    serializer_class = OpenStackServerSerializer

class OpenEdXInstanceViewSet(viewsets.ModelViewSet): #pylint: disable=no-init
    queryset = OpenEdXInstance.objects.all()
    serializer_class = OpenEdXInstanceSerializer
