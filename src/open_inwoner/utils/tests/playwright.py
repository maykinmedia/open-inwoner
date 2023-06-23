import importlib
import os
from typing import Callable, Dict, Iterable

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse

from furl import furl
from playwright.sync_api import Browser, Playwright, sync_playwright

from open_inwoner.accounts.models import User


class PlaywrightSyncLiveServerTestCase(StaticLiveServerTestCase):
    """
    base class for convenient synchronous Playwright in Django

    to help with debugging set the environment variable PWDEBUG=1 or PWDEBUG=console

    usage:

    from playwright.sync_api import expect

    class MyPageTest(PlaywrightSyncLiveServerTestCase):
        def test_my_page():
            # get a new context for test isolation
            context = self.browser.new_context()

            # open a page
            page = context.new_page()

            url = ...
            page.goto(url)

            # or more convenient:
            page.goto(self.live_url(path))
            page.goto(self.live_reverse("myapp:someobject_details", kwargs={"object_id": obj.id}, params={"query": "my keyword")))

            # do your things
            expect(page).to_have_title("Awesome title")
            ...

        def test_with_bsn_login():
            user = UserFactory.create(bsn="123456782")

            user_state = self.get_user_bsn_login_state(user)

            # user_state now has the cookies (etc) for the logged-in user and can be (re)used to get new context's
            context = self.browser.new_context(storage_state=user_state)
            ...
    """

    playwright: Playwright
    browser: Browser

    _old_async_unsafe: str

    @classmethod
    def launch_browser(cls, playwright):
        """
        extend and override to launch different browser for same case

        see also the @multi_browser()-decorator on how to automate browser variations

        using vanilla chromium as sane default
        """
        return playwright.chromium.launch()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # required for playwright cleanup
        cls._old_async_unsafe = os.environ.get("DJANGO_ALLOW_ASYNC_UNSAFE")
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

        cls.playwright = sync_playwright().start()
        cls.browser = cls.launch_browser(cls.playwright)

    @classmethod
    def tearDownClass(cls):
        if cls._old_async_unsafe is None:
            os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE")
        else:
            os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = cls._old_async_unsafe

        super().tearDownClass()

        cls.browser.close()
        cls.playwright.stop()

    @classmethod
    def live_url(cls, path="/", star=False):
        """
        prepend self.live_server_url to path
        optionally append '*' wildcard matcher (useful for page.wait_for_url() etc)
        """
        url = f"{cls.live_server_url}{path}"
        if star:
            url = f"{url}*"
        return url

    @classmethod
    def live_reverse(cls, viewname, args=None, kwargs=None, params=None, star=False):
        """
        do a reverse() url, prepend self.live_server_url
        optionally add query params to url
        optionally append '*' wildcard matcher (useful for page.wait_for_url() etc)
        """
        path = reverse(viewname, args=args, kwargs=kwargs)
        assert not (params and star), "cannot combine params and star arguments (yet)"
        url = cls.live_url(path, star=star)
        if params:
            url = furl(url).set(params).url
        return url

    @classmethod
    def get_user_bsn_login_state(cls, user: User):
        """
        login user with BSN via the digid-mock login flow and return the storage state.

        this storage state can be used to start a new context with the same cookies etc.

        to speed-up tests you can call this and save the output in setUpClass(cls).

        usage:
            user = UserFactory.create(bsn="123456782")

            user_logged_in = self.get_user_bsn_login_state(user)

            context = self.browser.new_context(storage_state=user_logged_in)
        """
        assert user.bsn, "user requires a BSN"
        assert user.pk, "user instance must be saved"

        context = cls.browser.new_context()
        page = context.new_page()

        page.goto(cls.live_reverse("digid:login"))

        page.get_by_text("Met gebruikersnaam en wachtwoord").click()

        page.wait_for_url(cls.live_reverse("digid-mock:password", star=True))

        page.get_by_text("DigiD gebruikersnaam", exact=True).fill(user.bsn)
        page.get_by_text("Wachtwoord", exact=True).fill("whatever")
        page.get_by_role("button", name="Inloggen").click()

        page.wait_for_url(cls.live_reverse("pages-root"))

        page.close()
        login_state = context.storage_state()
        context.close()
        return login_state


class Generated:
    pass


class multi_browser:
    """
    class-decorator to generate browser variations of test classes based on PlaywrightSyncLiveServerTestCase

    usage:

    @multi_browser()
    class MyPageTest(PlaywrightSyncLiveServerTestCase):
        pass

    """

    default_browsers = {
        "chromium": lambda p: p.chromium.launch(),
        "firefox": lambda p: p.firefox.launch(),
        "webkit": lambda p: p.webkit.launch(),
        "msedge": lambda p: p.chromium.launch(channel="msedge"),
        # MORE here, with interesting launch options
    }

    def __init__(self, extra_browsers: Dict[str, Callable] = None):
        # TODO support some options/settings here
        self.extra_browsers = extra_browsers

    @property
    def only_default(self):
        # ignore multi-browser (put in local.py for dev)
        return settings.PLAYWRIGHT_MULTI_ONLY_DEFAULT

    def get_browsers(self, cls) -> Iterable:
        if self.only_default:
            return []

        ret = self.default_browsers.copy()
        if self.extra_browsers:
            ret.update(self.extra_browsers)

        return ret.items()

    def __call__(self, cls):
        if not issubclass(cls, PlaywrightSyncLiveServerTestCase):
            # for now just test for our base-class, in the future we might be more flexible
            raise Exception(
                "decorated class must extend PlaywrightSyncLiveServerTestCase"
            )

        # import the (partially initialized) parent module
        module = importlib.import_module(cls.__module__)
        prefix = f"__{cls.__module__}."

        variations = self.get_browsers(cls)
        if not variations:
            # keep it if we don't have variations
            return cls

        for name, launcher in variations:
            # clean and generate new name
            new_name = "".join(c if c.isalnum() else "_" for c in name)
            new_name = f"{new_name[0].upper()}{new_name[1:]}"
            new_name = f"{prefix}{cls.__name__}__{new_name}"

            # new class
            inst_dict = {"launch_browser": launcher}
            new_type = type(
                new_name,
                (
                    Generated,
                    cls,
                ),
                inst_dict,
            )
            # update module
            # NOTE we add it to module but the generated class's string is still located here
            setattr(module, new_name, new_type)

        return cls
