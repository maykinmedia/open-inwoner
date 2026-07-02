from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from mozilla_django_oidc_db.constants import OIDC_ADMIN_CONFIG_IDENTIFIER
from mozilla_django_oidc_db.models import OIDCClient
from mozilla_django_oidc_db.tests.factories import OIDCClientFactory
from mozilla_django_oidc_db.tests.mixins import OIDCMixin

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.configurations.choices import OpenIDDisplayChoices
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.utils.test import ClearCachesMixin


@disable_admin_mfa()
class OIDCConfigTest(OIDCMixin, ClearCachesMixin, WebTest):
    csrf_checks = False

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        OIDCClientFactory(
            identifier=OIDC_ADMIN_CONFIG_IDENTIFIER,
            enabled=True,
            with_admin_options=True,
        )

    def test_admin_only_enabled(self):
        """Assert that the OIDC login option is only displayed for login via admin"""

        config = SiteConfiguration.get_solo()
        config.openid_display = OpenIDDisplayChoices.admin
        config.save()

        # regular site
        response = self.app.get(reverse("login"))

        self.assertNotContains(response, _("Inloggen met Azure AD"))

        # admin login
        response = self.app.get(reverse("admin:login"))

        oidc_login_option = response.pyquery.find(".admin-login-option")

        self.assertEqual(
            oidc_login_option.text(),
            "{} {}".format(_("or"), _("Login with organization account")),
        )

    def test_admin_only_disabled(self):
        """Assert that the OIDC login option is only displayed for regular users"""

        config = SiteConfiguration.get_solo()
        config.openid_display = OpenIDDisplayChoices.regular
        config.save()

        # regular site
        response = self.app.get(reverse("login"))

        link = response.pyquery.find("[title='Inloggen met Azure AD']")
        link_text = link.find(".link__text").text()

        self.assertEqual(link_text, "")

        # admin login
        response = self.client.get(reverse("admin:login"))

        self.assertNotContains(response, _("Login with organization account"))

    def test_oidc_config_validation(self):
        """
        Assert that error is displayed on attempt to select OIDC login for regular users
        if and only if `make_users_staff` is enabled in the admin OIDC configuration.
        """

        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.client.force_login(self.user)

        oidc_client = OIDCClient.objects.get(identifier=OIDC_ADMIN_CONFIG_IDENTIFIER)

        # case 1: `make_users_staff` is True
        oidc_client.options["groups_settings"]["make_users_staff"] = True
        oidc_client.save()

        url = reverse("admin:configurations_siteconfiguration_change")
        response = self.app.post(
            url, user=self.user, params={"openid_display": OpenIDDisplayChoices.regular}
        )

        field = response.pyquery(".field-openid_display")
        error_text = field.find(".errorlist").text()
        expected_error_text = _(
            "You cannot select this option if 'Make users staff' "
            "is selected in the OpenID Connect configuration."
        )

        self.assertEqual(expected_error_text, error_text)

        # case 2: `make_users_staff` is False
        oidc_client.options["groups_settings"]["make_users_staff"] = False
        oidc_client.save()

        response = self.client.post(
            url, user=self.user, data={"openid_display": "regular"}
        )

        self.assertNotContains(response, expected_error_text)
