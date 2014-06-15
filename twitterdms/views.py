from django.shortcuts import redirect, render
from django.http import HttpResponse

from django.views.generic import View
from django.contrib import messages

import tweepy

from django.conf import settings

from twitterdms import memory_cache
from twitterdms.forms import DMForm

consumer_key = settings.TWITTER_CONSUMER_KEY
consumer_secret = settings.TWITTER_CONSUMER_SECRET



class Home(View):
    def get(self, request):
        session = request.session
        
        authenticated = self.isAuthenticated()
        me_username = self.getUsername(request)
        auth_url = None

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

                    # Store the logged in username
                    session['me_username'] = auth.get_username()

                    return redirect('/')

                except tweepy.TweepError:
                    print 'Error! Failed to get access token.'

            else:  # show link to authorize
                callback_url = request.build_absolute_uri()
                auth = tweepy.OAuthHandler(consumer_key, consumer_secret, callback_url)
                auth_url = auth.get_authorization_url()
                session['request_token'] = (auth.request_token.key, auth.request_token.secret)

        form = DMForm(request)

        return render(request, 'twitterdms/home.html', {'authenticated': self.isAuthenticated(), 'auth_url': auth_url, 'form': form, 'me_username': me_username})


    def post(self, request):
        
        if not self.isAuthenticated():
            return HttpResponse('You need to authenticate first!')

        me_username = self.getUsername(request)
        form = DMForm(request, request.POST)

        if not form.is_valid():
            return render(request, 'twitterdms/home.html', {'authenticated': self.isAuthenticated(), 'auth_url': '', 
                                                            'form': form, 'me_username': me_username})

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token = request.session['access_token']
        access_token_secret = request.session['access_token_secret']

        auth.set_access_token(access_token, access_token_secret)

        self.api = tweepy.API(auth, cache=memory_cache)

        source = form.cleaned_data['users_source']
        msg = form.cleaned_data['dmtext']
        
        if source == 'Manual':
            users = form.cleaned_data['users']
        else:  # source = 'List' -- get users from lists
            users = self.getUsersFromListIDs(form.cleaned_data['lists'])


        errors = False
        for user in users:
            try:
                self.api.send_direct_message(user=user, text=msg)
            except tweepy.TweepError, e:
                errors = True
                if '34' in e.reason:
                    messages.error(request, 'User %s does not exist' % user, extra_tags='text-danger')
                elif '150' in e.reason:
                    messages.error(request, 'User %s is not following you' % user, extra_tags='text-danger')
                else:
                    messages.error(request, 'Unkown error when sending message to %s' % user, extra_tags='text-danger')

        if not errors:
            messages.success(request, 'Message was sent', extra_tags='text-success')

        return redirect('/')

        


    def isAuthenticated(self):
        return bool(self.request.session.get('access_token')) and bool(self.request.session.get('access_token_secret'))


    def getUsersFromListIDs(self, listIDs):
        users = set()

        for listID in listIDs:
            list_members = self.api.get_list(list_id=listID).members()
            for member in list_members:
                users.add(member.screen_name)

        return users

    def getUsername(self, request):
        if not self.isAuthenticated():
            return ''

        session = request.session

        if not 'me_username' in session:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            access_token = request.session['access_token']
            access_token_secret = request.session['access_token_secret']

            auth.set_access_token(access_token, access_token_secret)
            session['me_username'] = auth.get_username()

        return session['me_username']




def logout(request):
    session = request.session
    session.clear()

    return redirect('/')