from django.conf.urls import patterns, url
from . import views

from django.conf.urls import include
from rest_framework import routers

router = routers.DefaultRouter()

for er, eset in [
    (r'countries', views.CountryViewSet),
    (r'states', views.StateViewSet),
    (r'cities', views.CityViewSet),
    (r'bricks', views.BrickViewSet),
    (r'zips', views.ZipViewSet),

    (r'usercats', views.UserCatViewSet),
    (r'itemcats', views.ItemCatViewSet),
    (r'loccats', views.LocCatViewSet),
    (r'formcats', views.FormCatViewSet),

    (r'forcenodes', views.ForceNodeViewSet),
    (r'forcevisits', views.ForceVisitViewSet),

    (r'users', views.UserViewSet),
    (r'items', views.ItemViewSet),
    (r'locs', views.LocViewSet),

    (r'forms', views.FormViewSet),
    (r'formfields', views.FormFieldViewSet),
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
