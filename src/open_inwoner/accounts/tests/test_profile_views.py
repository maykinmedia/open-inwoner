import io

from django.test import override_settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

import requests_mock
from django_webtest import WebTest
from PIL import Image
from timeline_logger.models import TimelineLog
from webtest import Upload

from open_inwoner.accounts.choices import StatusChoices
from open_inwoner.haalcentraal.tests.mixins import HaalCentraalMixin
from open_inwoner.pdc.tests.factories import CategoryFactory
from open_inwoner.utils.logentry import LOG_ACTIONS

from ...questionnaire.tests.factories import QuestionnaireStepFactory
from ..choices import ContactTypeChoices, LoginTypeChoices
from ..forms import BrpUserForm, UserForm
from .factories import ActionFactory, DocumentFactory, UserFactory


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ProfileViewTests(WebTest):
    def setUp(self):
        self.url = reverse("profile:detail")
        self.return_url = reverse("logout")
        self.user = UserFactory(street="MyStreet")

        self.action_deleted = ActionFactory(
            name="deleted action, should not show up",
            created_by=self.user,
            is_deleted=True,
            status=StatusChoices.open,
        )

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_user_information_profile_page(self):
        response = self.app.get(self.url, user=self.user)

        self.assertContains(response, self.user.get_full_name())
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.phonenumber)
        self.assertContains(response, self.user.get_address())

    def test_get_empty_profile_page(self):
        response = self.app.get(self.url, user=self.user)

        self.assertEquals(response.status_code, 200)
        self.assertContains(response, _("U heeft geen interessegebieden aangegeven."))
        self.assertContains(response, _("U heeft nog geen contacten."))
        self.assertContains(response, "0 acties staan open.")
        self.assertNotContains(response, reverse("products:questionnaire_list"))

    def test_get_filled_profile_page(self):
        ActionFactory(created_by=self.user)
        contact = UserFactory()
        self.user.user_contacts.add(contact)
        category = CategoryFactory()
        self.user.selected_categories.add(category)
        QuestionnaireStepFactory(published=True)

        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, category.name)
        self.assertContains(
            response,
            f"{contact.first_name} ({contact.get_contact_type_display()})",
        )
        self.assertContains(response, "1 acties staan open.")
        self.assertContains(response, reverse("products:questionnaire_list"))

    def test_only_open_actions(self):
        action = ActionFactory(created_by=self.user, status=StatusChoices.closed)
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, "0 acties staan open.")

    def test_deactivate_account(self):
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

    def test_deactivate_account_digid(self):
        """
        check that user is redirected to digid:logout
        """
        user = UserFactory.create(
            login_type=LoginTypeChoices.digid, email="john@smith.nl"
        )

        response = self.app.get(self.url, user=user)
        self.assertEquals(response.status_code, 200)
        form = response.forms["deactivate-form"]

        response = form.submit()

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("digid:logout"))

    def test_get_documents_sorted(self):
        """
        check that the new document is shown first
        """
        doc_old = DocumentFactory.create(name="some-old", owner=self.user)
        doc_new = DocumentFactory.create(name="some-new", owner=self.user)

        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)

        file_tags = response.html.find(class_="file-list").find_all(
            class_="file-list__list-item"
        )
        self.assertEquals(len(file_tags), 2)
        self.assertTrue(doc_new.name in file_tags[0].prettify())
        self.assertTrue(doc_old.name in file_tags[1].prettify())

    def test_mydata_shown_with_digid_and_brp(self):
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=True,
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        self.assertContains(response, _("Mijn gegevens"))

    def test_mydata_not_shown_with_digid_and_no_brp(self):
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=False,
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        self.assertNotContains(response, _("Mijn gegevens"))

    def test_mydata_not_shown_without_digid(self):
        response = self.app.get(self.url, user=self.user)
        self.assertNotContains(response, _("Mijn gegevens"))

    def test_active_user_notifications_are_shown(self):
        response = self.app.get(self.url, user=self.user)
        self.assertContains(response, _("messages, plans"))

    def test_expected_message_is_shown_when_all_notifications_disabled(self):
        self.user.cases_notifications = False
        self.user.messages_notifications = False
        self.user.plans_notifications = False
        self.user.save()
        response = self.app.get(self.url, user=self.user)
        self.assertContains(response, _("You do not have any notifications enabled."))


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class EditProfileTests(WebTest):
    def setUp(self):
        self.url = reverse("profile:edit")
        self.return_url = reverse("profile:detail")
        self.user = UserFactory()

    def create_test_image_bytes(self):
        image = Image.new("RGB", (10, 10))
        byteIO = io.BytesIO()
        image.save(byteIO, format="png")
        return byteIO.getvalue()

    def upload_test_image_to_profile_edit_page(self, img_bytes):
        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]
        form["image"] = Upload("test_image.png", img_bytes, "image/png")
        response = form.submit()
        return response

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_save_form(self):
        response = self.app.get(self.url, user=self.user)
        self.assertEquals(response.status_code, 200)
        form = response.forms["profile-edit"]
        base_response = form.submit()
        self.assertEquals(base_response.url, self.return_url)
        followed_response = base_response.follow()
        self.assertEquals(followed_response.status_code, 200)

    def test_save_empty_form_fails(self):
        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]
        form["first_name"] = ""
        form["last_name"] = ""
        form["display_name"] = ""
        form["email"] = ""
        form["phonenumber"] = ""
        form["birthday"] = ""
        form["street"] = ""
        form["housenumber"] = ""
        form["postcode"] = ""
        form["city"] = ""
        base_response = form.submit()
        expected_errors = {"email": [_("Dit veld is vereist.")]}
        self.assertEqual(base_response.context["form"].errors, expected_errors)

    def test_save_filled_form(self):
        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]
        form["first_name"] = "First name"
        form["last_name"] = "Last name"
        form["display_name"] = "a nickname"
        form["email"] = "user@example.com"
        form["phonenumber"] = "06987878787"
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
        self.assertEquals(self.user.display_name, "a nickname")
        self.assertEquals(self.user.email, "user@example.com")
        self.assertEquals(self.user.birthday.strftime("%d-%m-%Y"), "21-01-1992")
        self.assertEquals(self.user.street, "Keizersgracht")
        self.assertEquals(self.user.housenumber, "17 d")
        self.assertEquals(self.user.postcode, "1013 RM")
        self.assertEquals(self.user.city, "Amsterdam")

    def test_save_with_invalid_first_name_chars_fails(self):
        invalid_characters = "/\"\\,.:;'"

        for char in invalid_characters:
            with self.subTest(char=char):
                response = self.app.get(self.url, user=self.user, status=200)
                form = response.forms["profile-edit"]
                form["first_name"] = char
                form["last_name"] = "Last name"
                form["display_name"] = "a nickname"
                form["phonenumber"] = "06987878787"
                form["birthday"] = "21-01-1992"
                form["street"] = "Keizersgracht"
                form["housenumber"] = "17 d"
                form["postcode"] = "1013 RM"
                form["city"] = "Amsterdam"
                response = form.submit()
                expected_errors = {
                    "first_name": [
                        _("Uw invoer bevat een ongeldig teken: {char}").format(
                            char=char
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    def test_save_with_invalid_last_name_chars_fails(self):
        invalid_characters = "/\"\\,.:;'"

        for char in invalid_characters:
            with self.subTest(char=char):
                response = self.app.get(self.url, user=self.user, status=200)
                form = response.forms["profile-edit"]
                form["first_name"] = "John"
                form["last_name"] = char
                form["display_name"] = "a nickname"
                form["phonenumber"] = "06987878787"
                form["birthday"] = "21-01-1992"
                form["street"] = "Keizersgracht"
                form["housenumber"] = "17 d"
                form["postcode"] = "1013 RM"
                form["city"] = "Amsterdam"
                response = form.submit()
                expected_errors = {
                    "last_name": [
                        _("Uw invoer bevat een ongeldig teken: {char}").format(
                            char=char
                        )
                    ]
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    def test_modify_email_succeeds(self):
        response = self.app.get(self.url, user=self.user)
        form = response.forms["profile-edit"]
        form["email"] = "user@example.com"
        response = form.submit()
        self.user.refresh_from_db()
        self.assertEqual(response.url, self.return_url)
        self.assertEqual(self.user.email, "user@example.com")

    def test_updating_a_field_without_modifying_email_succeeds(self):
        initial_email = self.user.email
        initial_first_name = self.user.first_name
        response = self.app.get(self.url, user=self.user)
        form = response.forms["profile-edit"]
        form["first_name"] = "Testing"
        response = form.submit()
        self.assertEqual(self.user.first_name, initial_first_name)
        self.user.refresh_from_db()
        self.assertEqual(response.url, self.return_url)
        self.assertEqual(self.user.email, initial_email)
        self.assertEqual(self.user.first_name, "Testing")

    def test_form_for_digid_brp_user_saves_data(self):
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=True,
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        form = response.forms["profile-edit"]

        form["display_name"] = "a nickname"
        form["email"] = "user@example.com"
        form["phonenumber"] = "06987878787"
        response = form.submit()

        self.assertEqual(response.url, self.return_url)

        user.refresh_from_db()

        self.assertEqual(user.display_name, "a nickname")
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.phonenumber, "06987878787")

    def test_expected_form_is_rendered(self):
        # regular user
        response = self.app.get(self.url, user=self.user)
        form = response.context["form"]

        self.assertEqual(type(form), UserForm)

        # digid-brp user
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=True,
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        form = response.context["form"]

        self.assertEqual(type(form), BrpUserForm)

    def test_image_is_saved_when_begeleider_and_default_login(self):
        self.user.contact_type = ContactTypeChoices.begeleider
        self.user.save()

        img_bytes = self.create_test_image_bytes()
        form_response = self.upload_test_image_to_profile_edit_page(img_bytes)

        self.assertRedirects(form_response, reverse("profile:detail"))
        with self.assertRaisesMessage(
            ValueError, "The 'image' attribute has no file associated with it."
        ):
            self.user.image.file

        self.user.refresh_from_db()

        self.assertIsNotNone(self.user.image.file)

    def test_image_is_saved_when_begeleider_and_digid_login(self):
        self.user.contact_type = ContactTypeChoices.begeleider
        self.user.login_type = LoginTypeChoices.digid
        self.user.save()

        img_bytes = self.create_test_image_bytes()
        form_response = self.upload_test_image_to_profile_edit_page(img_bytes)

        self.assertRedirects(form_response, reverse("profile:detail"))
        with self.assertRaisesMessage(
            ValueError, "The 'image' attribute has no file associated with it."
        ):
            self.user.image.file

        self.user.refresh_from_db()

        self.assertIsNotNone(self.user.image.file)

    def test_image_field_is_not_rendered_when_begeleider_and_default_login(self):
        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]

        self.assertNotIn("image", form.fields.keys())
        self.assertEqual(response.pyquery("#id_image"), [])

    def test_image_field_is_not_rendered_when_begeleider_and_digid_login(self):
        self.user.login_type = LoginTypeChoices.digid
        self.user.save()

        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]

        self.assertNotIn("image", form.fields.keys())
        self.assertEqual(response.pyquery("#id_image"), [])


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class MyDataTests(HaalCentraalMixin, WebTest):
    expected_response = {
        "first_name": "Merel",
        "initials": "M.",
        "last_name": "Kooyman",
        "prefix": None,
        "birthday": "10-04-1982",
        "birthday_place": "Leerdam",
        "gender": "vrouw",
        "street": "King Olivereiland",
        "house_number": 64,
        "postcode": "2551JV",
        "place": "'s-Gravenhage",
        "land": None,
    }

    def setUp(self):
        self.user = UserFactory(
            bsn="999993847",
            first_name="",
            last_name="",
            login_type=LoginTypeChoices.digid,
        )
        self.url = reverse("profile:data")

    def test_expected_response_is_returned_brp_v_2(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        response = self.app.get(self.url, user=self.user)
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            response.context["my_data"],
            self.expected_response,
        )
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user requests for brp data"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    @override_settings(BRP_VERSION="1.3")
    def test_expected_response_is_returned_brp_v_1_3(self, m):
        self._setUpMocks_v_1_3(m)
        self._setUpService()

        response = self.app.get(self.url, user=self.user)
        log_entry = TimelineLog.objects.last()

        self.assertEqual(
            response.context["my_data"],
            self.expected_response,
        )
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user requests for brp data"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )

    @override_settings(BRP_VERSION="1.3")
    def test_wrong_date_format_shows_birthday_none_brp_v_1_3(self, m):
        self._setUpService()

        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("personen_1.3.yaml"),
        )
        m.get(
            "https://personen/api/brp/ingeschrevenpersonen/999993847?fields=geslachtsaanduiding,naam,geboorte,verblijfplaats",
            status_code=200,
            json={
                "geboorte": {
                    "datum": {
                        "datum": "1982-04",
                    },
                }
            },
        )
        response = self.app.get(self.url, user=self.user)
        log_entry = TimelineLog.objects.last()

        self.assertIsNone(response.context["my_data"]["birthday"])
        self.assertEqual(
            log_entry.extra_data,
            {
                "message": _("user requests for brp data"),
                "action_flag": list(LOG_ACTIONS[4]),
                "content_object_repr": self.user.email,
            },
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class EditIntrestsTests(WebTest):
    def setUp(self):
        self.url = reverse("profile:categories")
        self.user = UserFactory()

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_preselected_values(self):
        category = CategoryFactory(name="a")
        CategoryFactory(name="b")
        CategoryFactory(name="c")
        self.user.selected_categories.add(category)
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-categories"]
        self.assertTrue(form.get("selected_categories", index=0).checked)
        self.assertFalse(form.get("selected_categories", index=1).checked)
        self.assertFalse(form.get("selected_categories", index=2).checked)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class EditNotificationsTests(WebTest):
    def setUp(self):
        self.url = reverse("profile:notifications")
        self.user = UserFactory()

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)

        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_default_values_for_regular_user(self):
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertTrue(form.get("messages_notifications").checked)
        self.assertTrue(form.get("plans_notifications").checked)
        self.assertNotIn("cases_notifications", form.fields)

    def test_disabling_notification_is_saved(self):
        self.assertTrue(self.user.messages_notifications)

        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]
        form["messages_notifications"] = False
        form.submit()

        self.user.refresh_from_db()

        self.assertTrue(self.user.cases_notifications)
        self.assertFalse(self.user.messages_notifications)
        self.assertTrue(self.user.plans_notifications)

    def test_cases_notifications_is_accessible_when_digid_user(self):
        self.user.login_type = LoginTypeChoices.digid
        self.user.save()
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertIn("cases_notifications", form.fields)


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ExportProfileTests(WebTest):
    def setUp(self):
        self.url = reverse("profile:export")
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
