from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa

from open_inwoner.accounts.tests.factories import UserFactory


@disable_admin_mfa()
class TestConfigurationColors(WebTest):
    def setUp(self):
        super().setUp()
        self.user = UserFactory(is_superuser=True, is_staff=True)

    def test_contrast_is_checked(self):
        response = self.app.get(
            # reverse list because django-solo
            reverse("admin:configurations_siteconfiguration_changelist"),
            user=self.user,
        )
        form = response.forms["siteconfiguration_form"]
        form["name"] = "xyz"
        form["primary_color"] = "#FFFFFF"
        form["primary_font_color"] = "#FFFFFF"
        form["secondary_color"] = "#FFFFFF"
        form["secondary_font_color"] = "#FFFFFF"
        form["accent_color"] = "#FFFFFF"
        form["accent_font_color"] = "#FFFFFF"
        response = form.submit("_continue").follow()

        messages = list(response.context["messages"])

        self.assertEqual(len(messages), 3 + 1)

        msg = messages[0]
        self.assertEqual(msg.level_tag, "warning")
        self.assertIn(str(_("Primary color")), msg.message)

        msg = messages[1]
        self.assertEqual(msg.level_tag, "warning")
        self.assertIn(str(_("Secondary color")), msg.message)

        msg = messages[2]
        self.assertEqual(msg.level_tag, "warning")
        self.assertIn(str(_("Accent color")), msg.message)
