from django.conf.urls import patterns, include, url
from django.views.generic.base import RedirectView

from django.contrib import admin
admin.autodiscover()






from django.views.generic.base import TemplateView
from lab import views






urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^lab/', include('lab.urls')),
    # url(r'^$', RedirectView.as_view(url='/lab', permanent=False), name='root'),

    url(r'^accounts/', include('allauth.urls')),




    url(r'^$', TemplateView.as_view(template_name='visitor/landing-index.html'), name='landing_index'),
    url(r'^about$', TemplateView.as_view(template_name='visitor/landing-about.html'), name='landing_about'),
    url(r'^terms/$', TemplateView.as_view(template_name='visitor/terms.html'), name='website_terms'),
    url(r'^contact$', TemplateView.as_view(template_name='visitor/contact.html'), name='website_contact'),

    url(r'^accounts/profile/$', views.account_profile, name='account_profile'),

    url(r'^member/$', views.member_index, name='user_home'),
    url(r'^member/action$', views.member_action, name='user_action'),

    url(r'^admin/', include(admin.site.urls)),
)
