from unittest.mock import patch

from django.conf import settings
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from django_webtest import WebTest
from freezegun.api import freeze_time
from furl.furl import furl
from pyquery.pyquery import PyQuery

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.mail.verification import (
    BadToken,
    decode_email_verification_token,
    generate_email_verification_token,
    generate_email_verification_url,
    send_user_email_verification_mail,
    validate_email_verification_token,
)
from open_inwoner.utils.url import set_next_url_param


class TestTokenVerification(TestCase):
    @freeze_time("2024-01-01 00:00")
    def test_generate_and_decode_token__basic(self):
        user = UserFactory.create(email="foo@example.com")

        token = generate_email_verification_token(user)
        payload = decode_email_verification_token(token)

        self.assertEqual(payload["u"], str(user.uuid))
        self.assertEqual(payload["e"], user.email)

        with freeze_time("2024-01-01 02:00"):
            with self.assertRaises(BadToken):
                decode_email_verification_token(token)

    def test_generate_email_verification_token__checks(self):
        with self.subTest("not active"):
            user = UserFactory.create(is_active=False)
            with self.assertRaises(BadToken):
                generate_email_verification_token(user)

        with self.subTest("no email"):
            user = UserFactory.create(email="")
            with self.assertRaises(BadToken):
                generate_email_verification_token(user)

        with self.subTest("already verified"):
            user = UserFactory.create(
                email="foo@example.com", verified_email="foo@example.com"
            )
            with self.assertRaises(BadToken):
                generate_email_verification_token(user)

        with self.subTest("verified email changed"):
            user = UserFactory.create(
                email="bar@example.com", verified_email="not_bar@example.com"
            )
            # got a token!
            self.assertNotEqual("", generate_email_verification_token(user))

    @freeze_time("2024-01-01 00:00")
    def test_validate_email_verification_token__basic(self):
        user = UserFactory.create(email="foo@example.com")
        self.assertFalse(user.has_verified_email())

        token = generate_email_verification_token(user)
        self.assertTrue(validate_email_verification_token(user, token))

        self.assertTrue(user.has_verified_email())
        self.assertEqual(user.email, user.verified_email)

    @freeze_time("2024-01-01 00:00")
    def test_validate_email_verification_token__combinations(self):
        user_one = UserFactory.create(email="foo@example.com")
        user_two = UserFactory.create(email="bar@example.com")

        token_one = generate_email_verification_token(user_one)
        token_two = generate_email_verification_token(user_two)

        with self.subTest("our own tokens are valid"):
            self.assertTrue(validate_email_verification_token(user_one, token_one))
            self.assertTrue(validate_email_verification_token(user_two, token_two))

        with self.subTest("expired tokens are invalid"):
            with freeze_time("2024-01-01 02:00"):
                self.assertFalse(validate_email_verification_token(user_one, token_one))
                self.assertFalse(validate_email_verification_token(user_two, token_two))

        with self.subTest("other tokens are invalid"):
            self.assertFalse(validate_email_verification_token(user_one, token_two))
            self.assertFalse(validate_email_verification_token(user_two, token_one))

        with self.subTest("broken tokens are invalid"):
            self.assertFalse(
                validate_email_verification_token(user_one, token_one[1:-1])
            )
            self.assertFalse(validate_email_verification_token(user_one, "dsfsfsfd"))
            self.assertFalse(validate_email_verification_token(user_one, ""))

    def test_validate_email_verification_token__checks(self):
        with self.subTest("deactivated"):
            user = UserFactory.create()
            token = generate_email_verification_token(user)
            user.is_active = False
            self.assertFalse(validate_email_verification_token(user, token))

        with self.subTest("no email"):
            user = UserFactory.create()
            token = generate_email_verification_token(user)
            user.email = ""
            self.assertFalse(validate_email_verification_token(user, token))

        with self.subTest("other email"):
            user = UserFactory.create(email="bar@example.com")
            token = generate_email_verification_token(user)
            user.email = "bazz@example.com"
            self.assertFalse(validate_email_verification_token(user, token))

    def test_user_has_verified_email(self):
        with self.subTest("verified"):
            user = UserFactory.create(
                email="foo@example.com", verified_email="foo@example.com"
            )
            self.assertTrue(user.has_verified_email())

        with self.subTest("no email"):
            user = UserFactory.create(email="", verified_email="")
            self.assertFalse(user.has_verified_email())

        with self.subTest("not verified"):
            user = UserFactory.create(email="bar@example.com", verified_email="")
            self.assertFalse(user.has_verified_email())

        with self.subTest("email changed"):
            user = UserFactory.create(
                email="bazz@example.com", verified_email="not_bazz@example.com"
            )
            self.assertFalse(user.has_verified_email())


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestSendVerificationEmail(WebTest):
    def get_sole_email_html_from_outbox(self, recipient):
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, [recipient])
        body = email.alternatives[0][0]  # html version of the email body
        return body

    def get_prefixed_url_from_html(self, html, url_prefix):
        pq = PyQuery(html)
        for elem in pq.find("a"):
            url = elem.attrib.get("href")
            if url and url_prefix in url:
                return url
        else:
            self.fail("could not locate URL in html")

    def test_send_user_email_verification_mail(self):
        user = UserFactory(email="foo@example.com")

        send_user_email_verification_mail(user)

        html = self.get_sole_email_html_from_outbox(user.email)

        url_path = reverse("mail:verification")
        self.assertIn(url_path, html)

        url = self.get_prefixed_url_from_html(html, url_path)
        response = self.app.get(url, user=user)

        user.refresh_from_db()
        self.assertTrue(user.has_verified_email())
        self.assertRedirects(response, reverse("pages-root"))

    def test_send_user_email_verification_mail__with_next_url(self):
        user = UserFactory(email="foo@example.com")

        target_url = reverse("profile:detail")
        send_user_email_verification_mail(user, target_url)

        html = self.get_sole_email_html_from_outbox(user.email)

        url_path = reverse("mail:verification")
        self.assertIn(url_path, html)

        url = self.get_prefixed_url_from_html(html, url_path)
        response = self.app.get(url, user=user)

        user.refresh_from_db()
        self.assertTrue(user.has_verified_email())

        self.assertRedirects(response, target_url)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestMailVerificationView(WebTest):
    def test_mail_verification_view(self):
        user = UserFactory(email="foo@example.com")
        self.assertFalse(user.has_verified_email())

        url = generate_email_verification_url(user)
        response = self.app.get(url, user=user)

        user.refresh_from_db()
        self.assertTrue(user.has_verified_email())

    def test_mail_verification_view__login_required(self):
        user = UserFactory(email="foo@example.com")
        url = generate_email_verification_url(user)
        response = self.app.get(url, status=302)
        expected = set_next_url_param(settings.LOGIN_URL, url)
        self.assertRedirects(response, expected)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class TestMailVerificationMiddlewareFlow(WebTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cms_tools.create_homepage()
        cms_tools.create_apphook_page(ProfileApphook)

        cls.url = reverse("pages-root")

    @patch(
        "open_inwoner.accounts.views.registration.send_user_email_verification_mail",
        autospec=True,
    )
    def test_verified_user_does_not_redirects(self, mock_send):
        config = SiteConfiguration.get_solo()
        user = UserFactory(email="foo@example.com", verified_email="foo@example.com")
        self.assertTrue(user.has_verified_email())

        # not required
        self.app.get(self.url, user=user, status=200)

        # with required
        config.email_verification_required = True
        config.save()

        self.app.get(self.url, user=user, status=200)

    @patch(
        "open_inwoner.accounts.views.registration.send_user_email_verification_mail",
        autospec=True,
    )
    def test_unverified_user_redirects(self, mock_send):
        config = SiteConfiguration.get_solo()
        user = UserFactory(email="foo@example.com")
        self.assertFalse(user.has_verified_email())

        # no redirect when not required
        self.app.get(self.url, user=user, status=200)

        # set required
        config.email_verification_required = True
        config.save()

        response = self.app.get(self.url, user=user)

        verify_url = reverse("profile:email_verification_user")
        self.assertRedirects(response, verify_url)

        response = response.follow()

        # email sent immediately on GET
        mock_send.assert_called_once_with(user, "")
        mock_send.reset_mock()

        response = response.forms["email-verification-form"].submit()

        # redirect to same page
        self.assertRedirects(response, verify_url + "?sent=1")
        response.follow(status=200)

        # email sent after submitting form
        mock_send.assert_called_once_with(user, "")

    @patch(
        "open_inwoner.accounts.views.registration.send_user_email_verification_mail",
        autospec=True,
    )
    def test_unverified_user_redirects__with_next_url(self, mock_send):
        config = SiteConfiguration.get_solo()
        config.email_verification_required = True
        config.save()

        user = UserFactory(email="foo@example.com")
        self.assertFalse(user.has_verified_email())

        # try to non-default page
        target_url = reverse("profile:detail")
        response = self.app.get(target_url, user=user)

        verify_url = reverse("profile:email_verification_user")
        f = furl(verify_url)
        f.args["next"] = target_url
        verify_url = f.url

        self.assertRedirects(response, verify_url)
        response = response.follow()

        # email sent immediately on GET request
        mock_send.assert_called_once_with(user, target_url)
        mock_send.reset_mock()

        response = response.forms["email-verification-form"].submit()

        # redirect to same page
        f = furl(verify_url)
        f.args["sent"] = 1
        self.assertRedirects(response, f.url)
        response.follow(status=200)

        # email sent after submitting form
        mock_send.assert_called_once_with(user, target_url)
