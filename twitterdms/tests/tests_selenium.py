import mock

from random import randint

from selenium import webdriver

from django.conf import settings
from django.test import LiveServerTestCase

class SeleniumTests(LiveServerTestCase):

    def authenticate(self):
        # John gets to the app homepage
        response = self.browser.get(self.live_server_url)

        # John clicks on the "Authenticate with Twitter" button
        auth_button = self.browser.find_element_by_id('twitterauth')
        auth_button.click()

        # He enters his credentials and clicks authorize
        username_input = self.browser.find_element_by_id('username_or_email')
        password_input = self.browser.find_element_by_id('password')
        authorize_button = self.browser.find_element_by_id('allow')

        username_input.send_keys(settings.TWITTER_TEST_USER)
        password_input.send_keys(settings.TWITTER_TEST_PASSWORD)
        authorize_button.click()

        self.browser.implicitly_wait(2)  # wait for redirection


    def setUp(self):
        super(SeleniumTests, self).setUp()
        self.browser = webdriver.Firefox()


    def tearDown(self):
        self.browser.quit()
        super(SeleniumTests, self).tearDown()


    def test_enable_disable_form(self):
        response = self.browser.get(self.live_server_url)

        users_input = self.browser.find_element_by_name('users')
        dmtext_input = self.browser.find_element_by_name('dmtext')

        self.assertFalse(users_input.is_enabled())
        self.assertFalse(dmtext_input.is_enabled())

        self.authenticate()

        users_input = self.browser.find_element_by_name('users')
        dmtext_input = self.browser.find_element_by_name('dmtext')

        self.assertTrue(users_input.is_enabled())
        self.assertTrue(dmtext_input.is_enabled())

    def test_can_logout(self):
        self.authenticate()

        logout_button = self.browser.find_element_by_id('logout')
        logout_button.click()

        self.assertIn('Login with Twitter', self.browser.page_source)



    @mock.patch('tweepy.API.send_direct_message')
    def test_user_can_send_single_dm(self, mock_send_dm):

        # John authenticates first
        self.authenticate()

        # John gets to the app homepage
        response = self.browser.get(self.live_server_url)

        users_input = self.browser.find_element_by_name('users')
        dmtext_input = self.browser.find_element_by_name('dmtext')


        # John fills the form with one user and a message
        users = settings.TWITTER_TEST_USERDMS[0]
        users_input.send_keys(users)

        dmtext = 'Hello world r %d' % randint(1, 200)
        dmtext_input.send_keys(dmtext)

        # John clicks on the "Send" button
        send_button = self.browser.find_element_by_name('submit').click()


        # John sees an info msg confirming that the msg was sent
        self.assertIn('Message was sent', self.browser.page_source)

        # Check that the message was actually sent
        self.assertEquals(mock_send_dm.call_count, 1)


    @mock.patch('tweepy.API.send_direct_message')
    def test_user_can_send_multiple_dm(self, mock_send_dm):

        # John authenticates first
        self.authenticate()

        # John gets to the app homepage
        response = self.browser.get(self.live_server_url)

        # He finds a page with fields for users and the DM text
        users_input = self.browser.find_element_by_name('users')
        dmtext_input = self.browser.find_element_by_name('dmtext')


        # John fills the form with multiple users, separated by commas and a message
        users = ', '.join(settings.TWITTER_TEST_USERDMS)
        users_input.send_keys(users)

        dmtext = 'Hello world r %d' % randint(1, 200)
        dmtext_input.send_keys(dmtext)

        # John clicks on the "Send" button
        send_button = self.browser.find_element_by_name('submit').click()


        # John sees an info msg confirming that the msg was sent
        self.assertIn('Message was sent', self.browser.page_source)

        # Check that the messages were sent
        self.assertEquals(mock_send_dm.call_count, 2)


    def test_layout_and_styling(self):
        # Edith goes to the home page
        self.browser.get(self.live_server_url)
        self.browser.set_window_size(1024, 768)

        users_input = self.browser.find_element_by_name('users')
        dmtext_input = self.browser.find_element_by_name('dmtext')

        # She notices the users input box is nicely centered
        self.assertAlmostEqual(
            users_input.location['x'] + users_input.size['width'] / 2,
            504,
            delta=5
        )

        # And the message input box too
        self.assertAlmostEqual(
            dmtext_input.location['x'] + dmtext_input.size['width'] / 2,
            504,
            delta=5
        )


    def test_clean_url_after_login(self):
        """
        Check that the user ends up in the root URL, without get
        params from oauth.
        """

        self.authenticate()

        self.assertEqual(self.browser.current_url, self.live_server_url + '/')
