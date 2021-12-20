from django.urls import reverse

from django_webtest import WebTest

from .factories import ContactFactory


class ContactViewTests(WebTest):
    def test_contact_list_login_required(self):
        login_url = reverse("login")
        url = reverse("accounts:contact_list")
        response = self.app.get(url)
        self.assertRedirects(response, f"{login_url}?next={url}")

    def test_contact_edit_login_required(self):
        contact = ContactFactory()
        login_url = reverse("login")
        url = reverse("accounts:contact_edit", kwargs={"uuid": contact.uuid})
        response = self.app.get(url)
        self.assertRedirects(response, f"{login_url}?next={url}")

    def test_contact_create_login_required(self):
        login_url = reverse("login")
        url = reverse("accounts:contact_create")
        response = self.app.get(url)
        self.assertRedirects(response, f"{login_url}?next={url}")
