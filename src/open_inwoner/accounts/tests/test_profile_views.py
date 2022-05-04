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
        self.return_url = reverse("logout")
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

    def test_only_open_actions(self):
        action = ActionFactory(created_by=self.user, status=StatusChoices.closed)
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "0 acties staan open.")

    def test_deactivate_account(self):
        self.app.set_user(user=self.user)  # Did not work without this..... No idea why?
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        form = response.forms["deactivate-form"]
        base_response = form.submit()
        self.assertEquals(base_response.url, self.return_url)
        followed_response = base_response.follow().follow()
        self.assertEquals(followed_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deactivated_on)

    def test_deactivate_account_staff(self):
        self.user.is_staff = True
        self.user.save()
        self.app.set_user(user=self.user)  # Did not work without this..... No idea why?
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        form = response.forms["deactivate-form"]
        base_response = form.submit()
        self.assertEquals(base_response.url, self.url)
        followed_response = base_response.follow()
        self.assertEquals(followed_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertIsNone(self.user.deactivated_on)


class EditProfileTests(WebTest):
    def setUp(self):
        self.url = reverse("accounts:edit_profile")
        self.return_url = reverse("accounts:my_profile")
        self.user = UserFactory()

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_save_form(self):
        self.app.set_user(user=self.user)  # Did not work without this..... No idea why?
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        form = response.forms["profile-edit"]
        base_response = form.submit()
        self.assertEquals(base_response.url, self.return_url)
        followed_response = base_response.follow()
        self.assertEquals(followed_response.status_code, 200)

    def test_save_empty_form(self):
        self.app.set_user(user=self.user)  # Did not work without this..... No idea why?
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        form = response.forms["profile-edit"]
        form["first_name"] = ""
        form["last_name"] = ""
        form["birthday"] = ""
        form["street"] = ""
        form["housenumber"] = ""
        form["postcode"] = ""
        form["city"] = ""
        base_response = form.submit()
        self.assertEquals(base_response.url, self.return_url)
        followed_response = base_response.follow()
        self.assertEquals(followed_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEquals(self.user.first_name, "")
        self.assertEquals(self.user.last_name, "")
        self.assertEquals(self.user.birthday, None)
        self.assertEquals(self.user.street, "")
        self.assertEquals(self.user.housenumber, "")
        self.assertEquals(self.user.postcode, None)
        self.assertEquals(self.user.city, "")

    def test_save_filled_form(self):
        self.app.set_user(user=self.user)  # Did not work without this..... No idea why?
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        form = response.forms["profile-edit"]
        form["first_name"] = "First name"
        form["last_name"] = "Last name"
        form["birthday"] = "21-01-1992"
        form["street"] = "Keizersgracht"
        form["housenumber"] = "17 d"
        form["postcode"] = "1013 RM"
        form["city"] = "Amsterdam"
        base_response = form.submit()
        self.assertEquals(base_response.url, self.return_url)
        followed_response = base_response.follow()
        self.assertEquals(followed_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEquals(self.user.first_name, "First name")
        self.assertEquals(self.user.last_name, "Last name")
        self.assertEquals(self.user.birthday.strftime("%d-%m-%Y"), "21-01-1992")
        self.assertEquals(self.user.street, "Keizersgracht")
        self.assertEquals(self.user.housenumber, "17 d")
        self.assertEquals(self.user.postcode, "1013 RM")
        self.assertEquals(self.user.city, "Amsterdam")


class EditIntrestsTests(WebTest):
    def setUp(self):
        self.url = reverse("accounts:my_themes")
        self.user = UserFactory()

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_preselected_values(self):
        category = CategoryFactory(name="a")
        CategoryFactory(name="b")
        CategoryFactory(name="c")
        self.app.set_user(user=self.user)  # Did not work without this..... No idea why?
        self.user.selected_themes.add(category)
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-themes"]
        self.assertTrue(form.get("selected_themes", index=0).checked)
        self.assertFalse(form.get("selected_themes", index=1).checked)
        self.assertFalse(form.get("selected_themes", index=2).checked)


class ExportProfileTests(WebTest):
    def setUp(self):
        self.url = reverse("accounts:profile_export")
        self.user = UserFactory()

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_export_profile(self):
        response = self.app.get(self.url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/pdf")
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="profile.pdf"',
        )
