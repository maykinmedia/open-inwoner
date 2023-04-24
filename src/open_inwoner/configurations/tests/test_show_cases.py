from unittest import skip

from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.choices import LoginTypeChoices
from open_inwoner.accounts.tests.factories import UserFactory

from ..models import SiteConfiguration


# TODO check this @skip
@skip("remove after move to django-cms")
class TestShowCases(WebTest):
    def setUp(self):
        self.user = UserFactory()
        self.config = SiteConfiguration.get_solo()

    def test_button_is_rendered_when_user_has_bsn_and_admin_allows_it(self):
        self.config.show_cases = True
        self.config.save()
        user = UserFactory(bsn="999999999", login_type=LoginTypeChoices.digid)

        response = self.app.get(reverse("root"), user=user)

        self.assertContains(response, _("Mijn aanvragen"))

    def test_button_is_not_rendered_when_user_has_bsn_and_admin_does_not_allow_it(self):
        self.config.show_cases = False
        self.config.save()
        user = UserFactory(bsn="999999999", login_type=LoginTypeChoices.digid)

        response = self.app.get(reverse("root"), user=user)

        self.assertNotContains(response, _("Mijn aanvragen"))

    def test_button_is_not_rendered_when_user_has_no_bsn_and_admin_allows_it(self):
        self.config.show_cases = True
        self.config.save()
        user = UserFactory()

        response = self.app.get(reverse("root"), user=user)

        self.assertNotContains(response, _("Mijn aanvragen"))

    def test_button_is_not_rendered_when_user_has_no_bsn_and_admin_does_not_allow_it(
        self,
    ):
        self.config.show_cases = False
        self.config.save()
        user = UserFactory()

        response = self.app.get(reverse("root"), user=user)

        self.assertNotContains(response, _("Mijn aanvragen"))

    def test_button_is_not_rendered_when_user_is_not_authenticated(
        self,
    ):
        self.config.show_cases = True
        self.config.save()

        response = self.app.get(reverse("root"))

        self.assertNotIn("_auth_user_id", self.app.session)
        self.assertNotContains(response, _("Mijn aanvragen"))
