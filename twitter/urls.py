from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'twitter.views.home', name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'', include('twitterdms.urls')),

)
