from django.shortcuts import redirect, render
from django.http import HttpResponse

from django.views.generic import View
from django.contrib import messages

import tweepy
import tweepy.api

from django.conf import settings

from twitterdms.forms import DMForm

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

        form = DMForm()
        return render(request, 'twitterdms/home.html', {'authenticated': self.isAuthenticated(), 'auth_url': auth_url, 'form': form})


    def post(self, request):
        
        if not self.isAuthenticated():
            return HttpResponse('You need to authenticate first!')

        form = DMForm(request.POST)

        if not form.is_valid():
            return render(request, 'twitterdms/home.html', {'authenticated': self.isAuthenticated(), 'auth_url': '', 'form': form})

        users = form.cleaned_data['users']
        msg = form.cleaned_data['dmtext']

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token = request.session['access_token']
        access_token_secret = request.session['access_token_secret']

        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth)

        errors = False
        for user in users:
            try:
                api.send_direct_message(user=user, text=msg)
            except tweepy.TweepError, e:
                errors = True
                if '34' in e.reason:
                    messages.error(request, 'User %s does not exist' % user)
                elif '150' in e.reason:
                    messages.error(request, 'User %s is not following you' % user)
                else:
                    messages.error(request, 'Unkown error when sending message to %s' % user)

        if not errors:
            messages.success(request, 'Message was sent')

        return redirect('/')

        


    def isAuthenticated(self):
        return bool(self.request.session.get('access_token')) and bool(self.request.session.get('access_token_secret'))


def logout(request):
    session = request.session
    session.clear()

    return redirect('/')