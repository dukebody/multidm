multidm
=======

Short: Django webapp to send Twitter DMs to multiple users.

I have observed that in many tweetstorm campaigns lots of DMs are sent to influential accounts to help with the campaign. There is an utility, [TweetGuru MultiDM], that lets you send DMs to multiple users, but entering only 12 each time, which can be too slow.

This app does not limit the number of users a DM can be sent to in one go. The only limitations come from Twitter itself, which only allows 250 DMs sent per day per user.


How to install
----------------

1. Clone this repository.
2. Using Python 2.7, ``pip install requirements.txt``.
3. Set the following environment variables: 
    1. ``DJANGO_SETTINGS_MODULE``: Python import path to the setting file. twitter.settings by default.
    2. ``TWITTER_CONSUMER_KEY`` and ``TWITTER_CONSUMER_SECRET``: key and secret of your own Twitter app (you will have to [create one] if you have not already done so).
4. (Optional) If you want to run the automated tests:
    1. ``TWITTER_TEST_USER`` and ``TWITTER_TEST_PASSWORD``: Twitter user and password for the Selenium tests.
    2. ``TWITTER_TEST_USERDMS``: users to try to send DMs to, separated by commas.
5. Start the Django app either using the dev server (``python manage.py runserver``) or any other more advanced server config you want. For example for gunicorn: ``foreman start``. You can also deploy this app to Heroku setting the previous environment vars in your app.
6. Enjoy!

[TweetGuru MultiDM]:http://tweetguru.net/multi/
[create one]:http://apps.twitter.com
