from django.conf.urls import patterns, url
from lab import views

from django.conf.urls import include
from rest_framework import routers

router = routers.DefaultRouter()

for er, eset in [
    (r'users', views.UserViewSet),
    (r'bricks', views.BrickViewSet),
]:
    router.register(er, eset)

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^setup$', views.setup, name='setup'),
    url(r'^agenda$', views.agenda, name='agenda'),
    url(r'^ajax$', views.ajax, name='ajax'),

    url(r'^api/', include(router.urls)),
)
# print 'urlpatterns', urlpatterns
