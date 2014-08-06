from django.conf.urls import patterns, url
from lab import views

from django.conf.urls import include
from rest_framework import routers

router = routers.DefaultRouter()

for er, eset in [
    (r'users', views.UserViewSet),
    (r'bricks', views.BrickViewSet),
    (r'doctor_cats', views.DoctorCatViewSet),
    (r'doctor_specialties', views.DoctorSpecialtyViewSet),
    (r'doctors', views.DoctorViewSet),
    (r'doctor_locs', views.DoctorLocViewSet),
    (r'item_cats', views.ItemCatViewSet),
    (r'item_subcats', views.ItemSubcatViewSet),
    (r'items', views.ItemViewSet),
    (r'markets', views.MarketViewSet),
    (r'forces', views.ForceViewSet),
    (r'force_mgrs', views.ForceMgrViewSet),
    (r'force_reps', views.ForceRepViewSet),
    (r'forms', views.FormViewSet),
    (r'form_fields', views.FormFieldViewSet),
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
