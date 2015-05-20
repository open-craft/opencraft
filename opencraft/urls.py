"""opencraft URL Configuration
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import RedirectView


urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('api.urls', namespace="api")),
    url(r'^task/', include('task.urls', namespace="task")),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon/favicon.ico', permanent=False)),
    url(r'^$', 'task.views.index'),
]
