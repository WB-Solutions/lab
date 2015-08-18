from django.conf.urls import patterns, url, include
from . import views
from . import api # REST.

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^setup$', views.setup, name='setup'),
    url(r'^agenda$', views.agenda, name='agenda'),
    url(r'^ajax$', views.ajax, name='ajax'),

    url(r'^goauth$', views.goauth, name='goauth'),

    url(r'^api/', include(api.router.urls)),
)
# print 'urlpatterns', urlpatterns
