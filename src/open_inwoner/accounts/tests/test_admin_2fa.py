from base64 import b32decode

from django.urls import reverse

from django_otp.oath import totp
from django_webtest import WebTest

from .factories import UserFactory


def get_wizard_form(response, prefix):
    return next(
        form
        for form in response.forms.values()
        if f"{prefix}-current_step" in form.fields
    )


class AdminTwoFactorWizardTests(WebTest):
    """
    The admin's 2FA login and setup are django-formtools wizards (through
    django-two-factor-auth and maykin-2fa), see #3088.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_staff=True, password="secret")

    def log_in_with_password(self):
        login_page = self.app.get(reverse("admin:login"))
        form = login_page.forms["login-form"]
        form["auth-username"] = self.user.email
        form["auth-password"] = "secret"
        return form.submit()

    def test_login_with_totp_device(self):
        device = self.user.totpdevice_set.create(name="default")

        token_page = self.log_in_with_password()

        form = token_page.forms["login-form"]
        form["token-otp_token"] = f"{totp(device.bin_key):06d}"
        response = form.submit()

        self.assertRedirects(
            response, reverse("admin:index"), fetch_redirect_response=False
        )

    def test_set_up_totp_device(self):
        response = self.log_in_with_password()

        self.assertRedirects(
            response, reverse("maykin_2fa:setup"), fetch_redirect_response=False
        )

        welcome_page = response.follow()
        method_page = get_wizard_form(welcome_page, "admin_setup_view").submit()

        form = get_wizard_form(method_page, "admin_setup_view")
        form["method-method"] = "generator"
        generator_page = form.submit()

        form = get_wizard_form(generator_page, "admin_setup_view")
        key = b32decode(generator_page.context["secret_key"])
        form["generator-token"] = f"{totp(key):06d}"
        response = form.submit()

        self.assertRedirects(
            response,
            reverse("maykin_2fa:setup_complete"),
            fetch_redirect_response=False,
        )
        self.assertEqual(
            list(self.user.totpdevice_set.values_list("name", "confirmed")),
            [("default", True)],
        )
