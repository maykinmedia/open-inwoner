from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from open_inwoner.accounts.choices import StatusChoices
from open_inwoner.accounts.models import Action
from open_inwoner.pdc.tests.factories import CategoryFactory

from .factories import ActionFactory, ContactFactory, UserFactory


class ProfileViewTests(WebTest):
    def setUp(self):
        self.url = reverse("accounts:my_profile")
        self.user = UserFactory()

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_get_empty_profile_page(self):
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, _("U heeft geen intressegebieden aangegeven."))
        self.assertContains(response, _("U heeft nog geen contacten."))
        self.assertContains(response, "0 acties staan open.")

    def test_get_filled_profile_page(self):
        action = ActionFactory(created_by=self.user)
        contact = ContactFactory(created_by=self.user)
        category = CategoryFactory()
        self.user.selected_themes.add(category)
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, category.name)
        self.assertContains(
            response,
            f"{contact.first_name} ({contact.get_type_display()})",
        )
        self.assertContains(response, "1 acties staan open.")

    def test_get_filled_profile_page(self):
        action = ActionFactory(created_by=self.user, status=StatusChoices.closed)
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "0 acties staan open.")
