import io

from django.urls import reverse
from django.utils.translation import ugettext as _

from django_webtest import WebTest
from PIL import Image
from webtest import Upload

from ..choices import ContactTypeChoices
from ..models import User
from .factories import UserFactory


class TestAdminUser(WebTest):
    def setUp(self):
        self.user = UserFactory(
            is_superuser=True, is_staff=True, email="john@example.com"
        )

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

    def test_user_not_updated_with_case_sensitive_email(self):
        response = self.app.get(
            reverse("admin:accounts_user_change", kwargs={"object_id": self.user.pk}),
            user=self.user,
        )
        form = response.forms["user_form"]
        form["email"] = "John@example.com"
        response = form.submit("_save")

        updated_user = User.objects.get()

        self.assertContains(response, _("The user with this email already exists."))
        self.assertEqual(self.user.email, updated_user.email)

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

        image = Image.new("RGB", (10, 10))
        byteIO = io.BytesIO()
        image.save(byteIO, format="png")
        img_bytes = byteIO.getvalue()

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
        image = Image.new("RGB", (10, 10))
        byteIO = io.BytesIO()
        image.save(byteIO, format="png")
        img_bytes = byteIO.getvalue()

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
