"""opencraft URL Configuration
"""
from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('api.urls', namespace="api")),
    url(r'^task/', include('task.urls', namespace="task")),
    url(r'^', 'task.views.index'),
]
