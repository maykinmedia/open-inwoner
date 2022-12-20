from django.conf import settings

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxDriver
from selenium.webdriver.remote.webdriver import WebDriver
from seleniumlogin import force_login as selenium_force_login


class SeleniumBrowserMixinBase:
    """
    shared baseclass for browser-specific selenium mixins

    expected to be mixed in with StaticLiveServerTestCase
    """

    selenium: WebDriver = None

    def force_login(self, user):
        selenium_force_login(user, self.selenium, self.live_server_url)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def tearDown(self):
        self.selenium.delete_all_cookies()


class FirefoxSeleniumMixin(SeleniumBrowserMixinBase):
    """
    usage: mix with your baseclass and StaticLiveServerTestCase

    example:

    class MyPageFirefoxTests(FirefoxSeleniumTests, BaseMyPageTests, StaticLiveServerTestCase):
        pass
    """

    options = FirefoxOptions()
    driver_class = FirefoxDriver

    @classmethod
    def setUpClass(cls):
        cls.options.headless = True
        if hasattr(settings, "FIREFOX_BINARY"):
            cls.options.binary = settings.FIREFOX_BINARY
        cls.selenium = cls.driver_class(options=cls.options)
        super().setUpClass()


class ChromeSeleniumMixin(SeleniumBrowserMixinBase):
    """
    usage: mix with your baseclass and StaticLiveServerTestCase

    example:

    class MyPageChromeTests(ChromeSeleniumTests, BaseMyPageTests, StaticLiveServerTestCase):
        pass
    """

    options = ChromeOptions()
    driver_class = ChromeDriver

    @classmethod
    def setUpClass(cls):
        cls.options.headless = True
        cls.selenium = cls.driver_class(options=cls.options)
        super().setUpClass()
