import mock

from selenium import webdriver

from django.conf import settings
from django.test import LiveServerTestCase

class SeleniumTests(LiveServerTestCase):

    def authenticate(self):
        # John gets to the app homepage
        self.browser.get(self.live_server_url)

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


    @mock.patch('tweepy.API.send_direct_message')
    def test_send_dm_to_users(self, mock_send_dm):

        # John gets to the front page
        self.browser.get(self.live_server_url)

        # He sees the inputs disabled
        users_input = self.browser.find_element_by_name('users')
        dmtext_input = self.browser.find_element_by_name('dmtext')

        self.assertFalse(users_input.is_enabled())
        self.assertFalse(dmtext_input.is_enabled())

        # So he decides to authenticate
        self.authenticate()

        
        # Check that the user ends up in the root URL, without get
        # params from oauth.
        
        self.assertEqual(self.browser.current_url, self.live_server_url + '/')

        # John gets to the app homepage
        self.browser.get(self.live_server_url)

        # Now the inputs are not disabled anymore
        users_input = self.browser.find_element_by_name('users')
        dmtext_input = self.browser.find_element_by_name('dmtext')

        self.assertTrue(users_input.is_enabled())
        self.assertTrue(dmtext_input.is_enabled())

        # John fills the form with multiple users, separated by commas and a message
        users = ', '.join(settings.TWITTER_TEST_USERDMS)
        users_input.send_keys(users)

        dmtext_input.send_keys('Hello world!')

        # John clicks on the "Send" button
        self.browser.find_element_by_name('submit').click()


        # John sees an info msg confirming that the msg was sent
        self.assertIn('Message was sent', self.browser.page_source)

        # Check that the messages were sent
        self.assertEquals(mock_send_dm.call_count, 2)

        # And he logs out
        logout_button = self.browser.find_element_by_id('logout')
        logout_button.click()

        self.assertIn('Login with Twitter', self.browser.page_source)


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
