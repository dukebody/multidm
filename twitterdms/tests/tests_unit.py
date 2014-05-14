import os
import importlib
import mock
from random import randint


from django.test import TestCase
from django.core.urlresolvers import resolve
from django.conf import settings

from tweepy.error import TweepError

from twitterdms.views import Home



# Create your tests here.


class HomePageTests(TestCase):

    def test_root_resolves_to_main_view(self):
        found = resolve('/')

        self.assertEqual(found.func.__name__, Home.as_view().__name__)

    def test_home_page_returns_correct_template(self):
        response = self.client.get('/')
        
        self.assertTemplateUsed(response, 'twitterdms/home.html')



class AuthTests(TestCase):

    def authenticate(self):
        session = self.client.session
        session['access_token'] = 'aaa'
        session['access_token_secret'] = 'bbb'
        session.save()

    def setUp(self):
        super(AuthTests, self).setUp()

        self.OLD_SESSION_ENGINE = settings.SESSION_ENGINE

        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = importlib.import_module('django.contrib.sessions.backends.file')
        store = engine.SessionStore()
        store.save()

        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key


    def tearDown(self):
        store = self.session
        os.unlink(store._key_to_file())

        settings.SESSION_ENGINE = self.OLD_SESSION_ENGINE
        
        super(AuthTests, self).tearDown()


    def test_not_authenticated_show_authbutton(self):
        response = self.client.get('/')

        self.assertContains(response, 'Login with Twitter')


    def test_already_authenticated_show_authenticated(self):
        self.authenticate()

        response = self.client.get('/')

        self.assertContains(response, 'Authenticated')


    @mock.patch('tweepy.API.send_direct_message')
    def test_not_authenticated_cannot_send_dms(self, mock_send_dm):
        users = settings.TWITTER_TEST_USERDMS[0]
        dmtext = 'Hello world r %d' % randint(1, 200)
        response = self.client.post('/', {'users': users, 'dmtext': dmtext })

        self.assertFalse(mock_send_dm.called)

        self.assertContains(response, 'You need to authenticate first!')
        self.assertNotContains(response, 'Message was sent')


    @mock.patch('tweepy.API.send_direct_message')
    def test_authenticated_can_send_dms(self, mock_send_dm):
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]
        dmtext = 'Hello world r %d' % randint(1, 200)
        response = self.client.post('/', {'users': users, 'dmtext': dmtext }, follow=True)

        self.assertTrue(mock_send_dm.called)

        self.assertContains(response, 'Message was sent')
        self.assertNotContains(response, 'You need to authenticate first!')


    @mock.patch('tweepy.API.send_direct_message')
    def test_home_page_send_message_multiple_users(self, mock_send_dm):
        self.authenticate()

        users = ', '.join(settings.TWITTER_TEST_USERDMS)
        dmtext = 'Hello world r %d' % randint(1, 200)
        response = self.client.post('/', {'users': users, 'dmtext': dmtext })
        
        # Check that the messages were sent
        self.assertEquals(mock_send_dm.call_count, 2)


    def test_noaccesstoken_oauthget_authbutton(self):
        """"
        Visiting the homepage with oauth parameters but no session access token set
        shows the "Authenticate" button
        """

        response = self.client.get('/?&oauth_verifier=kpdfsfgsvZCND992')

        self.assertContains(response, 'Login with Twitter')


    @mock.patch('tweepy.API.send_direct_message')
    def test_redirect_after_post(self, mock_send_dm):
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]
        dmtext = 'Hello world r %d' % randint(1, 200)
        response = self.client.post('/', {'users': users, 'dmtext': dmtext })

        self.assertRedirects(response, '/')


    @mock.patch('tweepy.API.send_direct_message')
    def test_success_msg_after_post(self, mock_send_dm):
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]
        dmtext = 'Hello world r %d' % randint(1, 200)
        response = self.client.post('/', {'users': users, 'dmtext': dmtext }, follow=True)

        msgs = response.context.get('messages')

        self.assertGreater(len(msgs),0)

    @mock.patch('tweepy.API.send_direct_message')
    def test_sending_too_long_msg_fails(self, mock_send_dm):
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]
        dmtext = 'This message is larger than 140 chars. This message is larger than 140 chars. This message is larger than 140 chars. This message is larger than 140 chars.'

        response = self.client.post('/', {'users': users, 'dmtext': dmtext }, follow=True)

        self.assertFalse(mock_send_dm.called)
        self.assertContains(response, 'Message is too long')

    @mock.patch('tweepy.API.send_direct_message')
    def test_send_invalid_users_fails(self, mock_send_dm):
        self.authenticate()

        users = 'this is not a valid, '
        dmtext = 'Test message'

        response = self.client.post('/', {'users': users, 'dmtext': dmtext }, follow=True)

        self.assertFalse(mock_send_dm.called)
        self.assertContains(response, 'not valid Twitter usernames')

    @mock.patch('tweepy.API.send_direct_message', side_effect=TweepError(u'34'))
    def test_send_unexistent_user_fails_nicely(self, mock_send_dm):
        self.authenticate()

        users = '@unexistent_user'
        dmtext = 'Test message'

        response = self.client.post('/', {'users': users, 'dmtext': dmtext }, follow=True)

        self.assertContains(response, 'does not exist')

    @mock.patch('tweepy.API.send_direct_message', side_effect=TweepError(u'150'))
    def test_send_nonfollower_fails_nicely(self, mock_send_dm):
        self.authenticate()

        users = '@nytimes'
        dmtext = 'Test message'

        response = self.client.post('/', {'users': users, 'dmtext': dmtext }, follow=True)


        self.assertContains(response, 'is not following you')