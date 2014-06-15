import re
from django import forms
from django.conf import settings

import tweepy

from twitterdms import memory_cache

consumer_key = settings.TWITTER_CONSUMER_KEY
consumer_secret = settings.TWITTER_CONSUMER_SECRET


# http://stackoverflow.com/questions/2304632/regex-for-twitter-username
TWITTER_USERNAME_RE = re.compile(r'(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z]+[A-Za-z0-9]+)')


class MultiTwitterUsernameField(forms.Field):
    """
    List of Twitter usenames, separated by commas.
    """

    def to_python(self, value):
        "Normalize data to a list of strings."

        # Return an empty list if no input was given.
        if not value:
            return []

        return [u.strip() for u in value.split(',')]

    def validate(self, value):
        "Check if value consists only of valid Twitter usernames."

        # Use the parent's handling of required fields, etc.
        super(MultiTwitterUsernameField, self).validate(value)

        invalid_usernames = []
        
        for username in value:
            if not TWITTER_USERNAME_RE.match(username):
                invalid_usernames.append(username)


        if invalid_usernames:
            raise forms.ValidationError("%s are not valid Twitter usernames" % ', '.join(invalid_usernames))



class DMForm(forms.Form):

    def __init__(self, request, *args, **kwargs):
        super(DMForm, self).__init__(*args, **kwargs)
        self.request = request

        self.fields['lists'] = forms.MultipleChoiceField(
            label='Lists',
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'list-inline'}),
            error_messages={
                'invalid_choice': 'Please select at least one valid list to send the message to'
            },
            choices=self.getListsChoices()
        )

    users_source = forms.ChoiceField(
        label='Users source',
        choices=(
            ('Manual','Manual'),
            ('List', 'List'),
        ),
        initial='Manual',
        widget=forms.RadioSelect(attrs={'class': 'form-control'}),
        error_messages={
            'required': 'Please specify a valid user source',
            'invalid_choice': 'Please specify a valid user source'
        }
    )

    users = MultiTwitterUsernameField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': '@user1, @user2, @user3...'})
    )
    
    dmtext = forms.CharField(
        max_length=140, 
        label='Message', 
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': "Don't get over 140 chars!"}),
        error_messages={'max_length':'Message is too long'}
        )

    def getListsChoices(self):
        if not self.isAuthenticated():
            return []
        
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        access_token = self.request.session['access_token']
        access_token_secret = self.request.session['access_token_secret']

        auth.set_access_token(access_token, access_token_secret)

        api = tweepy.API(auth, cache=memory_cache)

        lists = api.lists_all()

        return [(l.id, l.name) for l in lists]



    def isAuthenticated(self):
        return bool(self.request.session.get('access_token')) and bool(self.request.session.get('access_token_secret'))

    def clean(self):
        """
        Check that:
         * If source is manual, users are specified
         * If source is list, at least one list is selected
        """

        data = self.cleaned_data

        source = data.get('users_source')
        users = data.get('users')
        lists = data.get('lists')

        if source == 'Manual' and not users:
            raise forms.ValidationError('Please specify at least one user')

        if source == 'List' and not lists:
            raise forms.ValidationError('Please specify at least one list')

        return data