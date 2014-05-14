import re
from django import forms

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
    users = MultiTwitterUsernameField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': '@user1, @user2, @user3...'}))
    dmtext = forms.CharField(
            max_length=140, 
            label='Message', 
            widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': "Don't get over 140 chars!"}),
            error_messages={'max_length':'Message is too long'}
            )