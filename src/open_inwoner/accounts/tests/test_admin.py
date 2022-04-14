from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_webtest import WebTest

from ..models import Contact
from .factories import ContactFactory, UserFactory


class TestContactValidation(WebTest):
    def setUp(self):
        self.user = UserFactory(is_superuser=True, is_staff=True)
        self.contact = ContactFactory.build()

    def test_contact_is_saved_without_email_provided(self):
        url = reverse("admin:accounts_contact_add")
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        form["created_by"] = self.user.id
        response = form.submit()
        self.assertRedirects(response, reverse("admin:accounts_contact_changelist"))
        self.assertEquals(Contact.objects.count(), 1)

    def test_contact_is_not_saved_with_email_and_missing_contact_user(self):
        url = reverse("admin:accounts_contact_add")
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        form["email"] = self.contact.email
        form["created_by"] = self.user.id
        response = form.submit()
        self.assertEquals(
            response.context["errors"],
            [[_('"Contact gebruiker" is mandatory when "E-mailadres" is filled in.')]],
        )
        self.assertEquals(Contact.objects.count(), 0)

    def test_contact_is_not_saved_with_email_and_different_contact_user(self):
        other_user = UserFactory()
        url = reverse("admin:accounts_contact_add")
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        form["email"] = self.contact.email
        form["created_by"] = self.user.id
        form["contact_user"] = other_user.id
        response = form.submit()
        self.assertEquals(
            response.context["errors"],
            [
                [
                    _(
                        'The email addresses of "E-mailadres" and "Contact gebruiker" do not match.'
                    )
                ]
            ],
        )
        self.assertEquals(Contact.objects.count(), 0)

    def test_contact_is_not_saved_with_contact_user_and_missing_email(self):
        url = reverse("admin:accounts_contact_add")
        form = self.app.get(url, user=self.user).forms.get("contact_form")
        form["first_name"] = self.contact.first_name
        form["last_name"] = self.contact.last_name
        form["created_by"] = self.user.id
        form["contact_user"] = self.user.id
        response = form.submit()
        self.assertEquals(
            response.context["errors"],
            [
                [
                    _(
                        'The email addresses of "E-mailadres" and "Contact gebruiker" do not match.'
                    )
                ]
            ],
        )
        self.assertEquals(Contact.objects.count(), 0)
