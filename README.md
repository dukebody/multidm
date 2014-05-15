multidm
=======

Short: Django webapp to send Twitter DMs to multiple users.

I have observed that in many tweetstorm campaigns lots of DMs are sent to influential accounts to help with the campaign. There is an utility, [TweetGuru MultiDM], that lets you send DMs to multiple users, but entering only 12 each time, which can be too slow.

This app does not limit the number of users a DM can be sent to in one go. The only limitations come from Twitter itself, which only allows 250 DMs sent per day per user.


How to install
----------------

1. Clone this repository.
2. Using Python 2.7, ``pip install requirements.txt``  (Django 1.6 and tweepy)
3. Copy ``twitter/config.example.py`` to ``twitter/config.py`` and enter the consumer key and secret for your own Twitter app (you will have to [create one] if you have not already done so).
4. Start the Django app either using the dev server (``python manage.py runserver``) or any other more advanced server config you want.
5. Enjoy!

[TweetGuru MultiDM]:http://tweetguru.net/multi/
[create one]:http://apps.twitter.com
