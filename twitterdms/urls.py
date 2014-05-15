from django.conf.urls import patterns, include, url

from twitterdms.views import Home, logout


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'twitter.views.home', name='home'),
    url(r'^$', Home.as_view(), name="home"),
    url(r'^logout$', logout, name="logout"),
)
