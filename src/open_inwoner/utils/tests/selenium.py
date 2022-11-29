from django.conf import settings

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeDriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxDriver


class FirefoxSeleniumTests:
    """
    usage: mix with your base class and StaticLiveServerTestCase

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


class ChromeSeleniumTests:
    """
    usage: mix with your base class and StaticLiveServerTestCase

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
