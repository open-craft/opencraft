from django.conf.urls import include, url
from django.views.generic.base import RedirectView

from .router import router

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='v1/', permanent=False), name='index'),
    url(r'^v1/', include(router.urls)),
    url(r'^v1/auth/', include('rest_framework.urls', namespace='rest_framework')),
]
