from django.urls import reverse
from django.utils.translation import gettext as _

from django_webtest import WebTest
from maykin_2fa.test import disable_admin_mfa
from webtest import Upload

from open_inwoner.accounts.choices import ContactTypeChoices, DigitalAddressType
from open_inwoner.accounts.models import User
from open_inwoner.utils.tests.helpers import create_image_bytes

from .factories import DigitalAddressFactory, UserFactory


@disable_admin_mfa()
class TestAdminUser(WebTest):
    def setUp(self):
        self.user = UserFactory(
            is_superuser=True, is_staff=True, email="john@example.com"
        )
        self.assertEqual(User.objects.count(), 1)

    def test_user_is_created_without_case_sensitive_email(self):
        response = self.app.get(reverse("admin:accounts_user_add"), user=self.user)
        form = response.forms["user_form"]
        form["email"] = "john2@example.com"
        form["password1"] = "Abc123!@#"
        form["password2"] = "Abc123!@#"
        response = form.submit("_save")

        self.assertEqual(User.objects.count(), 2)

    def test_user_is_updated_without_case_sensitive_email(self):
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "john2@example.com"
        response = form.submit("_save")

        existing_user = User.objects.get()

        self.assertEqual(existing_user.email, "john2@example.com")

    def test_user_is_updated_without_modifying_email(self):
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["first_name"] = "Updated"
        response = form.submit("_save")

        existing_user = User.objects.get()

        self.assertEqual(existing_user.first_name, "Updated")
        self.assertEqual(existing_user.email, self.user.email)

    def test_user_not_created_with_case_sensitive_email(self):
        response = self.app.get(reverse("admin:accounts_user_add"), user=self.user)
        form = response.forms["user_form"]
        form["email"] = "John@example.com"
        form["password1"] = "Abc123!@#"
        form["password2"] = "Abc123!@#"
        response = form.submit("_save")

        self.assertContains(response, _("The user with this email already exists."))
        self.assertEqual(User.objects.count(), 1)

    def test_user_can_change_case_of_own_email(self):
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "John@example.com"
        form.submit("_save")

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "John@example.com")

    def test_user_not_updated_with_case_variant_of_other_users_email(self):
        other = UserFactory(email="jane@example.com")
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": other.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "John@example.com"
        response = form.submit("_save")

        self.assertContains(response, _("This email is already taken."))
        other.refresh_from_db()
        self.assertEqual(other.email, "jane@example.com")

    def test_user_not_updated_with_digital_address_of_other_user(self):
        DigitalAddressFactory(user=self.user, value="john.secondary@example.com")
        other = UserFactory(email="jane@example.com")
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": other.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "john.secondary@example.com"
        response = form.submit("_save")

        self.assertContains(response, _("This email is already taken."))
        other.refresh_from_db()
        self.assertEqual(other.email, "jane@example.com")

    def test_email_change_updates_standard_digital_address(self):
        self.user.update_email(self.user.email)
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "john2@example.com"
        form.submit("_save")

        self.assertEqual(
            list(
                self.user.digital_addresses.values_list(
                    "type", "value", "is_standard_for_type"
                )
            ),
            [(DigitalAddressType.email, "john2@example.com", True)],
        )

    def test_validation_error_is_raised_when_wrong_format_email(self):
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "John@example"
        response = form.submit("_save")

        self.assertContains(response, _("Voer een geldig e-mailadres in."))

    def test_begeleider_can_add_an_image(self):
        self.user.contact_type = ContactTypeChoices.begeleider
        self.user.save()

        img_bytes = create_image_bytes()

        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )

        form = response.forms["user_form"]
        form["image"] = Upload("test_image.png", img_bytes, "image/png")
        response = form.submit("_save")

        self.assertRedirects(response, reverse("admin:accounts_user_changelist"))
        with self.assertRaises(ValueError):
            self.user.image.file

        self.user.refresh_from_db()

        self.assertIsNotNone(self.user.image.file)

    def test_non_begeleider_cannot_add_an_image(self):
        img_bytes = create_image_bytes()

        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )

        form = response.forms["user_form"]
        form["image"] = Upload("test_image.png", img_bytes, "image/png")
        response = form.submit("_save")

        self.assertEqual(
            response.context["errors"][0][0],
            _("Only a 'begeleider' user can add an image."),
        )

        self.user.refresh_from_db()

        with self.assertRaises(ValueError):
            self.user.image.file
