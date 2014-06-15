import os
import importlib
import mock

from django.test import TestCase
from django.core.urlresolvers import resolve
from django.conf import settings

from tweepy.error import TweepError

from twitterdms.views import Home
from twitterdms.forms import DMForm



# Create your tests here.

DMTEXT = 'Hello World!'
LISTS_CHOICES = (
        ('0', 'List 1'),
        ('1', 'List 2'),
    )

TWITTER_ACCESS_TOKEN = getattr(settings, 'TWITTER_ACCESS_TOKEN', '')
TWITTER_ACCESS_TOKEN_SECRET = getattr(settings, 'TWITTER_ACCESS_TOKEN_SECRET', '')


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
        session['access_token'] = TWITTER_ACCESS_TOKEN
        session['access_token_secret'] = TWITTER_ACCESS_TOKEN_SECRET
        session['me_username'] = 'myusername'
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


    @mock.patch('tweepy.API.lists_all', return_value=[])
    def test_already_authenticated_show_authenticated_get(self, la_mock):
        self.authenticate()

        response = self.client.get('/')

        self.assertContains(response, 'Authenticated as @')
        self.assertNotContains(response, 'nobody')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    def test_already_authenticated_show_authenticated_post(self, la_mock):
        self.authenticate()

        response = self.client.post('/')

        self.assertContains(response, 'Authenticated as @')
        self.assertNotContains(response, 'nobody')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    def test_user_can_logout(self, la_mock):
        self.authenticate()

        response = self.client.get('/logout', follow=True)

        self.assertContains(response, 'Login with Twitter')

    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_not_authenticated_cannot_send_dms(self, mock_send_dm, la_mock):
        users = settings.TWITTER_TEST_USERDMS[0]
        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual' })

        self.assertFalse(mock_send_dm.called)

        self.assertContains(response, 'You need to authenticate first!')
        self.assertNotContains(response, 'Message was sent')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_authenticated_can_send_dms(self, mock_send_dm, la_mock):
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]
        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual'}, follow=True)

        self.assertTrue(mock_send_dm.called)

        self.assertContains(response, 'Message was sent')
        self.assertNotContains(response, 'You need to authenticate first!')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_home_page_send_message_multiple_users(self, mock_send_dm, la_mock):
        self.authenticate()

        users = ', '.join(settings.TWITTER_TEST_USERDMS)
        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual'})
        
        # Check that the messages were sent
        self.assertEquals(mock_send_dm.call_count, 2)


    @mock.patch('twitterdms.views.Home.getUsersFromListIDs', return_value=['user1', 'user2'])
    @mock.patch('twitterdms.forms.DMForm.getListsChoices', 
        return_value=LISTS_CHOICES)
    @mock.patch('tweepy.API.send_direct_message')
    def test_home_page_send_list(self, mock_send_dm, la_mock, mock_userids):
        self.authenticate()

        self.client.post('/', {'dmtext': DMTEXT, 'users_source': 'List', 'lists': '0'})
        
        # Check that the messages were sent
        self.assertTrue(mock_send_dm.called)
        self.assertEquals(mock_send_dm.call_count, 2)


    @mock.patch('twitterdms.forms.DMForm.getListsChoices', return_value=LISTS_CHOICES)
    @mock.patch('tweepy.API.send_direct_message')
    def test_home_page_send_list_fails_if_no_list_specified(self, mock_send_dm, la_mock):
        self.authenticate()

        self.client.post('/', {'dmtext': DMTEXT, 'users_source': 'List'})
        
        # Check that the messages were sent
        self.assertFalse(mock_send_dm.called)


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_sending_without_specifying_source_fails(self, mock_send_dm, la_mock):
        """
        Don't send if the request doesn't specify the source of users
        """
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]

        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT }, follow=True)

        self.assertFalse(mock_send_dm.called)
        self.assertContains(response, 'Please specify a valid user source')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_sending_without_specifying_valid_source_fails(self, mock_send_dm, la_mock):
        """
        Don't send if the request doesn't specify a valid user source
        """
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]

        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'My ass'}, follow=True)

        self.assertFalse(mock_send_dm.called)
        self.assertContains(response, 'Please specify a valid user source')


    def test_noaccesstoken_oauthget_authbutton(self):
        """"
        Visiting the homepage with oauth parameters but no session access token set
        shows the "Authenticate" button
        """

        response = self.client.get('/?&oauth_verifier=kpdfsfgsvZCND992')

        self.assertContains(response, 'Login with Twitter')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_redirect_after_post(self, mock_send_dm, la_mock):
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]
        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual'})

        self.assertRedirects(response, '/')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_success_msg_after_post(self, mock_send_dm, la_mock):
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]
        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual'}, follow=True)

        msgs = response.context.get('messages')

        self.assertGreater(len(msgs),0)


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_sending_too_long_msg_fails(self, mock_send_dm, la_mock):
        self.authenticate()

        users = settings.TWITTER_TEST_USERDMS[0]
        dmtext = 'This message is larger than 140 chars. This message is larger than 140 chars. This message is larger than 140 chars. This message is larger than 140 chars.'

        response = self.client.post('/', {'users': users, 'dmtext': dmtext, 'users_source': 'Manual'}, follow=True)

        self.assertFalse(mock_send_dm.called)
        self.assertContains(response, 'Message is too long')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message')
    def test_send_invalid_users_fails(self, mock_send_dm, la_mock):
        self.authenticate()

        users = 'this is not a valid, '

        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual'}, follow=True)

        self.assertFalse(mock_send_dm.called)
        self.assertContains(response, 'not valid Twitter usernames')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message', side_effect=TweepError(u'34'))
    def test_send_unexistent_user_fails_nicely(self, mock_send_dm, la_mock):
        self.authenticate()

        users = '@unexistent_user'

        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual' }, follow=True)

        self.assertContains(response, 'does not exist')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message', side_effect=TweepError(u'150'))
    def test_send_nonfollower_fails_nicely(self, mock_send_dm, la_mock):
        self.authenticate()

        users = '@nytimes'

        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual'}, follow=True)


        self.assertContains(response, 'is not following you')


    @mock.patch('tweepy.API.lists_all', return_value=[])
    @mock.patch('tweepy.API.send_direct_message', side_effect=TweepError(u'666'))
    def test_send_unknown_error_fails_nicely(self, mock_send_dm, la_mock):
        self.authenticate()

        users = '@whatever'

        response = self.client.post('/', {'users': users, 'dmtext': DMTEXT, 'users_source': 'Manual'}, follow=True)

        self.assertContains(response, 'Unkown error when sending message to')


    def unauth_user_has_no_lists(self):
        response = self.client.get('/')
        form = DMForm(response.request)

        lists_choices = form.getListsChoices()

        self.assertEqual(lists_choices, [])