"""
Override those URLs we want to override. /peterbe
"""

from django.conf import settings
from django.conf.urls.defaults import patterns, url
from . import views


urlpatterns = patterns('',
                       url(r'^accounts/login/$',
                           views.login,
                           name='login'),
                       )

if settings.CAN_REGISTER:
    urlpatterns += patterns('',
                       url(r'^accounts/register/?$',
                           views.register,
                           name='registration_register'),
                       )
