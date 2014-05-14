from django.shortcuts import redirect, render
from django.http import HttpResponse

from django.views.generic import View
from django.contrib import messages

import tweepy
import tweepy.api

from django.conf import settings

consumer_key = settings.TWITTER_CONSUMER_KEY
consumer_secret = settings.TWITTER_CONSUMER_SECRET

# Create your views here.

class Home(View):
    def get(self, request):
        authenticated = self.isAuthenticated()
        auth_url = None

        session = request.session


        if not authenticated:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            oauth_verifier = request.GET.get('oauth_verifier')
            token = session.get('request_token')
            
            if oauth_verifier and token:  # just back from Twitter's auth page
                session.delete('request_token')
                auth.set_request_token(token[0], token[1])

                try:
                    auth.get_access_token(oauth_verifier)
                    session['access_token'] = auth.access_token.key
                    session['access_token_secret'] = auth.access_token.secret

                except tweepy.TweepError:
                    print 'Error! Failed to get access token.'

            else:  # show link to authorize
                callback_url = request.build_absolute_uri()
                auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
                auth_url = auth.get_authorization_url()
                session['request_token'] = (auth.request_token.key, auth.request_token.secret)


        return render(request, 'twitterdms/home.html', {'authenticated': self.isAuthenticated(), 'auth_url': auth_url})


    def post(self, request):
        
        if not self.isAuthenticated():
            return HttpResponse('You need to authenticate first!')

        users = request.POST['users']
        msg = request.POST['dmtext']

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token = request.session['access_token']
        access_token_secret = request.session['access_token_secret']

        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)

        users = [u.strip() for u in users.split(',')]

        for user in users:
            api.send_direct_message(user=user, text=msg)

        messages.success(request, 'Message was sent')
        return redirect('/')


    def isAuthenticated(self):
        return bool(self.request.session.get('access_token')) and bool(self.request.session.get('access_token_secret'))