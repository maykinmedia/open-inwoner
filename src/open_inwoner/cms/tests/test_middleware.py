from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from maykin_2fa.test import disable_admin_mfa
from pyquery import PyQuery as pq

from open_inwoner.cms.tests import cms_tools
from open_inwoner.cms.utils.middleware import DropToolbarMiddleware
from open_inwoner.utils.tests.helpers import TwoFactorUserTestMixin


class TestDropToolbarMiddleware(TwoFactorUserTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cms_tools.create_homepage()
        cls.url = reverse("pages-root")

    def test_middleware_is_mounted(self):
        cls = DropToolbarMiddleware
        path = f"{cls.__module__}.{cls.__name__}"
        self.assertIn(path, settings.MIDDLEWARE)

    def test_anon_shows_no_toolbar(self):
        response = self.client.get(self.url)

        self.assertNotHasToolbar(response)

    @disable_admin_mfa()
    def test_not_staff_not_verified_no_2fa_shows_no_toolbar(self):
        self.create_user()
        self.login_user()
        response = self.client.get(self.url)

        self.assertNotHasToolbar(response)

    @disable_admin_mfa()
    def test_staff_not_verified_no_2fa_shows_toolbar(self):
        self.create_user(is_staff=True)
        self.login_user()
        response = self.client.get(self.url)

        self.assertHasToolbar(response)

    @override_settings(MAYKIN_2FA_ALLOW_MFA_BYPASS_BACKENDS=[])
    def test_staff_not_verified_with_2fa_shows_no_toolbar(self):
        self.create_user(is_staff=True)
        self.login_user()
        response = self.client.get(self.url)

        self.assertNotHasToolbar(response)

    def test_staff_verified_with_2fa_shows_toolbar(self):
        self.create_user(is_staff=True)
        self.enable_otp()
        self.login_user()
        response = self.client.get(self.url)

        self.assertHasToolbar(response)

    def assertHasToolbar(self, response):
        d = pq(response.content.decode("utf8"))
        if not len(d(".cms-toolbar")):
            self.fail("cannot locate element with class '.cms-toolbar'")

    def assertNotHasToolbar(self, response):
        d = pq(response.content.decode("utf8"))
        if len(d(".cms-toolbar")):
            self.fail("found element with class '.cms-toolbar'")
