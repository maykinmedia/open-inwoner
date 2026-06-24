from dataclasses import asdict
from datetime import date
from unittest.mock import patch

from django import forms
from django.conf import settings
from django.template.defaultfilters import date as django_date
from django.test import TestCase, override_settings, tag
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import WebTest
from freezegun import freeze_time
from pyquery import PyQuery
from webtest import Upload

from open_inwoner.accounts.brp import BRPData
from open_inwoner.accounts.choices import (
    ContactTypeChoices,
    DigitalAddressType,
    LoginTypeChoices,
    NotificationChannelChoice,
    StatusChoices,
)
from open_inwoner.accounts.forms import (
    BrpUserForm,
    EmailDigitalAddressFormSet,
    PhoneDigitalAddressFormSet,
    UserForm,
)
from open_inwoner.accounts.models import DigitalAddress, User
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.collaborate.cms_apps import CollaborateApphook
from open_inwoner.cms.inbox.cms_apps import InboxApphook
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.haalcentraal.tests.mixins import HaalCentraalMixin
from open_inwoner.laposta.models import LapostaConfig
from open_inwoner.laposta.tests.factories import LapostaListFactory, MemberFactory
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.models import (
    DigitaalAdresOpenKlantMapping,
    ESuiteKlantConfig,
)
from open_inwoner.openklant.tests.data import MockAPIReadPatchData
from open_inwoner.openklant.tests.factories import DigitaalAdresOpenKlantMappingFactory
from open_inwoner.pdc.tests.factories import CategoryFactory
from open_inwoner.plans.tests.factories import PlanFactory
from open_inwoner.qmatic.tests.data import QmaticMockData
from open_inwoner.questionnaire.tests.factories import QuestionnaireStepFactory
from open_inwoner.utils.forms import ErrorMessageMixin
from open_inwoner.utils.logentry import LOG_ACTIONS
from open_inwoner.utils.test import ClearCachesMixin
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin, create_image_bytes

from .factories import (
    ActionFactory,
    DigidUserFactory,
    DigitalAddressFactory,
    UserFactory,
    eHerkenningUserFactory,
)

# Avoid redirects through `KvKLoginMiddleware`
PATCHED_MIDDLEWARE = [
    m
    for m in settings.MIDDLEWARE
    if m != "open_inwoner.kvk.middleware.KvKLoginMiddleware"
]


@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls", MIDDLEWARE=PATCHED_MIDDLEWARE
)
class ProfileViewTests(WebTest):
    def setUp(self):
        self.url = reverse("profile:detail")
        self.return_url = reverse("logout_confirm")
        self.user = UserFactory(
            first_name="Erik", street="MyStreet", messages_notifications=True
        )
        self.digid_user = DigidUserFactory()
        self.eherkenning_user = eHerkenningUserFactory()

        self.action_deleted = ActionFactory(
            name="deleted action, should not show up",
            created_by=self.user,
            is_deleted=True,
            status=StatusChoices.open,
        )

        cms_tools.create_homepage()

        self.profile_app = ProfileConfig.objects.create(
            namespace=ProfileApphook.app_name
        )
        cms_tools.create_apphook_page(ProfileApphook)

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_show_logout_link_in_header(self):
        """All login types show a link to the logout confirm page in the header."""
        confirm_url = reverse("logout_confirm")
        eidas_user = UserFactory(
            login_type=LoginTypeChoices.eidas_person_bsn,
            bsn="123456789",
            eidas_pseudo_id="eidas-test",
        )

        for user in [self.user, self.digid_user, self.eherkenning_user, eidas_user]:
            with self.subTest(login_type=user.login_type):
                response = self.app.get(self.url, user=user)
                logout_link = response.pyquery.find(f"a[href='{confirm_url}']")
                self.assertIsNotNone(logout_link.attr["href"])

    @patch(
        "open_inwoner.cms.utils.page_display.inbox_page_is_published", return_value=True
    )
    def test_user_information_profile_page(self, m):
        email_da = DigitalAddressFactory(
            user=self.user,
            type=DigitalAddressType.email,
            value=self.user.email,
            is_standard_for_type=True,
        )
        alt_email_da = DigitalAddressFactory(
            user=self.user,
            type=DigitalAddressType.email,
            value="alt@example.com",
            is_standard_for_type=False,
        )
        phone_da = DigitalAddressFactory(
            user=self.user,
            type=DigitalAddressType.phone,
            value="0612345678",
            is_standard_for_type=True,
        )
        response = self.app.get(self.url, user=self.user)

        self.assertContains(response, self.user.first_name)
        self.assertContains(response, f"Welkom, {self.user.display_name}")
        self.assertContains(response, f"{self.user.infix} {self.user.last_name}")
        self.assertContains(response, self.user.street)
        self.assertContains(response, self.user.housenumber)
        self.assertContains(response, self.user.city)

        doc = PyQuery(response.content)
        personal_section = doc.find(".profile-section__personal-info")

        # standard email shown with (voorkeur) marker; alt email shown without
        self.assertContains(response, f"{email_da.value} (voorkeur)")
        self.assertNotContains(response, f"{alt_email_da.value} (voorkeur)")

        # phone shown
        self.assertIn(phone_da.value, personal_section.text())

        # check business profile section not displayed
        self.assertNotContains(response, "Bedrijfsgegevens")

        # check notification preferences displayed
        notifications_text = doc.find("#profile-notifications")[0].text_content()
        self.assertIn("Mijn Berichten", notifications_text)

    @patch(
        "open_inwoner.cms.utils.page_display.inbox_page_is_published", return_value=True
    )
    def test_admin_disable_options(self, m):
        config = SiteConfiguration.get_solo()
        config.notifications_actions_enabled = False
        config.notifications_cases_enabled = False
        config.notifications_messages_enabled = False
        config.notifications_plans_enabled = False
        config.save()

        response = self.app.get(self.url, user=self.user)

        doc = PyQuery(response.content)

        self.assertEqual(doc.find("#profile-notifications"), [])

    def test_get_empty_profile_page(self):
        response = self.app.get(self.url, user=self.user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("U heeft geen interesses gekozen."))
        self.assertContains(response, _("U heeft nog geen contacten"))
        self.assertContains(response, "0 acties staan open")
        self.assertNotContains(response, reverse("products:questionnaire_list"))

    def test_get_filled_profile_page(self):
        ActionFactory(created_by=self.user)
        contact = UserFactory()
        self.user.user_contacts.add(contact)
        category = CategoryFactory()
        self.user.selected_categories.add(category)
        QuestionnaireStepFactory(published=True)
        cms_tools.create_apphook_page(ProductsApphook)

        response = self.app.get(self.url, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, category.name)
        self.assertContains(
            response,
            f"{contact.first_name} ({contact.get_contact_type_display()})",
        )
        self.assertContains(response, "1 acties staan open")
        self.assertContains(response, reverse("products:questionnaire_list"))

    def test_only_open_actions(self):
        ActionFactory(created_by=self.user, status=StatusChoices.closed)
        response = self.app.get(self.url, user=self.user)
        self.assertIn("0 acties staan open", response)

    def test_mydata_shown_with_digid_and_brp(self):
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=True,
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        self.assertContains(response, _("Bekijk alle gegevens"))

        # check business profile section not displayed
        self.assertNotContains(response, "Bedrijfsgegevens")

    def test_mydata_not_shown_with_digid_and_no_brp(self):
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=False,
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        self.assertNotContains(response, _("My details"))

    def test_mydata_not_shown_without_digid(self):
        response = self.app.get(self.url, user=self.user)
        self.assertNotContains(response, _("My details"))

    def test_info_eherkenning_user(self):
        user = eHerkenningUserFactory(
            kvk="11111111",
            company_name="Makers and Shakers",
            street="Fantasiestraat",
            housenumber="42",
            postcode="1234 XY",
            city="The good place",
        )
        response = self.app.get(self.url, user=user)

        self.assertContains(response, "Makers and Shakers")
        self.assertContains(response, "Fantasiestraat 42")
        self.assertContains(response, "1234 XY The good place")

        doc = PyQuery(response.content)

        business_section = doc.find("#business-overview")[0]
        self.assertEqual(business_section.text.strip(), "Bedrijfsgegevens")

        # check personal overview section not displayed
        personal_section = doc.find("#personal-overview")
        self.assertEqual(personal_section, [])

    @patch("open_inwoner.cms.utils.page_display._is_published", return_value=True)
    def test_active_user_notifications_are_shown(self, mock_page_display):
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=False,
            login_type=LoginTypeChoices.digid,
            messages_notifications=True,
            plans_notifications=True,
            cases_notifications=False,
        )
        response = self.app.get(self.url, user=user)
        self.assertContains(response, _("Mijn Berichten, Samenwerken"))

    def test_expected_message_is_shown_when_all_notifications_disabled(self):
        self.user.cases_notifications = False
        self.user.messages_notifications = False
        self.user.plans_notifications = False
        self.user.save()
        response = self.app.get(self.url, user=self.user)
        self.assertContains(response, _("You do not have any notifications enabled."))

    def test_messages_enabled_disabled(self):
        """Assert that `Stuur een bericht` is displayed if and only if the message page is published"""

        begeleider = UserFactory(contact_type=ContactTypeChoices.begeleider)
        self.user.user_contacts.add(begeleider)

        # case 1: no message page
        response = self.app.get(self.url, user=self.user)

        self.assertNotContains(response, _("Stuur een bericht"))

        # case 2: unpublished message page
        page = cms_tools.create_apphook_page(InboxApphook, publish=False)

        response = self.app.get(self.url, user=self.user)

        self.assertNotContains(response, _("Stuur een bericht"))

        # case 3: published message page
        cms_tools.publish_page(page, "nl")

        response = self.app.get(self.url, user=self.user)

        message_link = response.pyquery("[title='Stuur een bericht']")
        link_text = message_link.find(".link__text").text

        self.assertEqual(link_text(), _("Stuur een bericht"))


@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls", MIDDLEWARE=PATCHED_MIDDLEWARE
)
class EditProfileTests(AssertTimelineLogMixin, WebTest):
    def setUp(self):
        self.url = reverse("profile:edit")
        self.return_url = reverse("profile:detail")
        self.user = UserFactory()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _da_formset_data(prefix, entries, initial_pks=None):
        """
        Build POST data for a DigitalAddress inline formset.

        entries: list of (value, is_standard) tuples for each form row.
        initial_pks: list of existing DigitalAddress PKs (None for new rows).
        """
        initial_pks = initial_pks or [None] * len(entries)
        initial_count = sum(1 for pk in initial_pks if pk is not None)
        data = {
            f"{prefix}-TOTAL_FORMS": str(len(entries)),
            f"{prefix}-INITIAL_FORMS": str(initial_count),
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
        }
        for i, ((value, is_standard), pk) in enumerate(zip(entries, initial_pks)):
            if pk is not None:
                data[f"{prefix}-{i}-id"] = str(pk)
            if value:
                data[f"{prefix}-{i}-value"] = value
            if is_standard:
                data[f"{prefix}-{i}-is_standard_for_type"] = "on"
        return data

    def _empty_da_formsets(self):
        """Management form data for two empty formsets (no initial, no new entries)."""
        data = {}
        data.update(self._da_formset_data("email_addresses", []))
        data.update(self._da_formset_data("phone_addresses", []))
        return data

    def upload_test_image_to_profile_edit_page(self, img_bytes):
        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]
        form["image"] = Upload("test_image.png", img_bytes, "image/png")
        response = form.submit()
        return response

    # -------------------------------------------------------------------------
    # Basic access / render
    # -------------------------------------------------------------------------

    def test_login_required(self):
        login_url = reverse("login")
        response = self.app.get(self.url)
        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_save_form(self):
        response = self.app.get(self.url, user=self.user)
        self.assertEqual(response.status_code, 200)
        form = response.forms["profile-edit"]
        base_response = form.submit()
        self.assertEqual(base_response.url, self.return_url)
        followed_response = base_response.follow()
        self.assertEqual(followed_response.status_code, 200)

    def test_expected_form_is_rendered(self):
        # regular user
        response = self.app.get(self.url, user=self.user)
        self.assertEqual(type(response.context["form"]), UserForm)

        # digid-brp user
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=True,
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        self.assertEqual(type(response.context["form"]), BrpUserForm)

    def test_context_contains_da_formsets(self):
        response = self.app.get(self.url, user=self.user)
        self.assertIsInstance(
            response.context["email_formset"], EmailDigitalAddressFormSet
        )
        self.assertIsInstance(
            response.context["phone_formset"], PhoneDigitalAddressFormSet
        )

    # -------------------------------------------------------------------------
    # DA formset validation
    # -------------------------------------------------------------------------

    def test_email_formset_rejects_duplicate_values(self):
        self.client.force_login(self.user)
        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data.update(
            self._da_formset_data(
                "email_addresses",
                [("dup@example.com", True), ("dup@example.com", False)],
            )
        )
        data.update(self._da_formset_data("phone_addresses", []))

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["email_formset"].is_valid())

    def test_phone_formset_rejects_multiple_standard_entries(self):
        self.client.force_login(self.user)
        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data.update(self._da_formset_data("email_addresses", []))
        data.update(
            self._da_formset_data(
                "phone_addresses",
                [("0612345678", True), ("0687654321", True)],
            )
        )

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["phone_formset"].is_valid())

    def test_email_formset_rejects_invalid_format(self):
        self.client.force_login(self.user)
        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data.update(
            self._da_formset_data(
                "email_addresses",
                [("not-an-email", True)],
            )
        )
        data.update(self._da_formset_data("phone_addresses", []))

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["email_formset"].is_valid())

    def test_phone_formset_rejects_invalid_format(self):
        self.client.force_login(self.user)
        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data.update(self._da_formset_data("email_addresses", []))
        data.update(
            self._da_formset_data(
                "phone_addresses",
                [("not-a-phone", True)],
            )
        )

        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["phone_formset"].is_valid())

    # -------------------------------------------------------------------------
    # Saving address changes
    # -------------------------------------------------------------------------

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_save_filled_form(self, mock_update):
        mock_update.return_value = True

        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]
        form["first_name"] = "First name"
        form["last_name"] = "Last name"
        form["email_addresses-0-value"] = "user@example.com"
        form["email_addresses-0-is_standard_for_type"] = True
        form["phone_addresses-0-value"] = "0612345678"
        form["phone_addresses-0-is_standard_for_type"] = True
        form["street"] = "Keizersgracht"
        form["housenumber"] = "17 d"
        form["postcode"] = "1013 RM"
        form["city"] = "Amsterdam"
        base_response = form.submit()

        self.assertEqual(base_response.url, self.return_url)
        followed_response = base_response.follow()
        self.assertEqual(followed_response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "First name")
        self.assertEqual(self.user.last_name, "Last name")
        self.assertEqual(self.user.display_name, "First name")
        self.assertEqual(self.user.email, "user@example.com")
        self.assertEqual(self.user.phonenumber, "0612345678")
        self.assertEqual(self.user.street, "Keizersgracht")
        self.assertEqual(self.user.housenumber, "17 d")
        self.assertEqual(self.user.postcode, "1013 RM")
        self.assertEqual(self.user.city, "Amsterdam")

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_save_with_primary_and_alternative_phone(self, mock_update):
        """Two phone DA entries: one standard, one non-standard."""
        from open_inwoner.accounts.models import DigitalAddress, DigitalAddressType

        mock_update.return_value = True

        data = {
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        data.update(self._da_formset_data("email_addresses", []))
        data.update(
            self._da_formset_data(
                "phone_addresses",
                [("0612345678", True), ("0687654321", False)],
            )
        )
        self.client.force_login(self.user)
        response = self.client.post(self.url, data=data)

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phonenumber, "0612345678")
        alt = DigitalAddress.objects.filter(
            user=self.user,
            type=DigitalAddressType.phone,
            is_standard_for_type=False,
        ).first()
        self.assertIsNotNone(alt)
        self.assertEqual(alt.value, "0687654321")

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_modify_email_succeeds(self, mock_update):
        mock_update.return_value = True

        response = self.app.get(self.url, user=self.user)
        form = response.forms["profile-edit"]
        form["email_addresses-0-value"] = "user@example.com"
        form["email_addresses-0-is_standard_for_type"] = True
        response = form.submit()

        self.user.refresh_from_db()
        self.assertEqual(response.url, self.return_url)
        self.assertEqual(self.user.email, "user@example.com")

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_modify_contact_details_eherkenning_succeeds(self, mock_update):
        mock_update.return_value = True

        eherkenning_user = eHerkenningUserFactory()
        response = self.app.get(self.url, user=eherkenning_user)
        form = response.forms["profile-edit"]
        form["email_addresses-0-value"] = "user@example.com"
        form["email_addresses-0-is_standard_for_type"] = True
        form["phone_addresses-0-value"] = "0612345678"
        form["phone_addresses-0-is_standard_for_type"] = True
        response = form.submit()

        eherkenning_user.refresh_from_db()
        self.assertEqual(response.url, self.return_url)
        self.assertEqual(eherkenning_user.email, "user@example.com")
        self.assertEqual(eherkenning_user.phonenumber, "0612345678")

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_updating_a_field_without_modifying_email_succeeds(self, mock_update):
        mock_update.return_value = True

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

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_form_for_digid_brp_user_saves_data(self, mock_update):
        mock_update.return_value = True
        user = UserFactory(
            bsn="999993847",
            first_name="name",
            last_name="surname",
            is_prepopulated=True,
            login_type=LoginTypeChoices.digid,
        )
        response = self.app.get(self.url, user=user)
        form = response.forms["profile-edit"]

        # first_name is not rendered for digid_brp_user
        with self.assertRaises(AssertionError):
            form["first_name"] = "test"

        form["email_addresses-0-value"] = "user@example.com"
        form["email_addresses-0-is_standard_for_type"] = True
        form["phone_addresses-0-value"] = "0612345678"
        form["phone_addresses-0-is_standard_for_type"] = True
        response = form.submit()

        self.assertEqual(response.url, self.return_url)
        user.refresh_from_db()
        self.assertEqual(user.display_name, "name")
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.phonenumber, "0612345678")

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_brp_user_with_diacritics_in_name_can_submit_edit_profile_form(
        self, mock_update
    ):
        mock_update.return_value = True

        user = DigidUserFactory(
            first_name="Liselotte-Anne Daniëlle Celèste Elise 26 Avril Stéphane Maroni jr.",
            infix="Isiah dé Maria de las Mercedes Rosalía",
            last_name="J'adore Grace a Dieu Rhiannon San-che-he-ray Lou'Lou Elona L'vovna d'Alessandra Ariëlle",
        )
        response = self.app.get(self.url, user=user)
        form = response.forms["profile-edit"]

        # BrpUserForm does not include name fields for BRP users
        with self.assertRaises(AssertionError):
            form["first_name"]

        form["email_addresses-0-value"] = "updated@example.com"
        form["email_addresses-0-is_standard_for_type"] = True
        response = form.submit()

        self.assertEqual(response.url, self.return_url)

        user.refresh_from_db()
        self.assertEqual(user.email, "updated@example.com")
        self.assertEqual(
            user.first_name,
            "Liselotte-Anne Daniëlle Celèste Elise 26 Avril Stéphane Maroni jr.",
        )
        self.assertEqual(user.infix, "Isiah dé Maria de las Mercedes Rosalía")
        self.assertEqual(
            user.last_name,
            "J'adore Grace a Dieu Rhiannon San-che-he-ray Lou'Lou Elona L'vovna d'Alessandra Ariëlle",
        )

    def test_name_validation(self):
        invalid_characters = '<>#/"\\,.:;'

        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]

        for char in invalid_characters:
            with self.subTest(char=char):
                form["first_name"] = "test" + char
                form["infix"] = char + "test"
                form["last_name"] = "te" + char + "st"
                form["city"] = "te" + char + "st"
                form["street"] = "te" + char + "st"

                response = form.submit()

                error_msg = _(
                    "Please make sure your input contains only valid characters "
                    "(letters, numbers, apostrophe, dash, space)."
                )
                expected_errors = {
                    "first_name": [error_msg],
                    "infix": [error_msg],
                    "last_name": [error_msg],
                    "city": [error_msg],
                    "street": [error_msg],
                }
                self.assertEqual(response.context["form"].errors, expected_errors)

    # -------------------------------------------------------------------------
    # Image upload
    # -------------------------------------------------------------------------

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_image_is_saved_when_begeleider_and_default_login(self, mock_update):
        mock_update.return_value = True
        self.user.contact_type = ContactTypeChoices.begeleider
        self.user.save()

        img_bytes = create_image_bytes()
        form_response = self.upload_test_image_to_profile_edit_page(img_bytes)

        self.assertRedirects(form_response, reverse("profile:detail"))
        with self.assertRaisesMessage(
            ValueError, "The 'image' attribute has no file associated with it."
        ):
            self.user.image.file

        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.image.file)

    @patch(
        "open_inwoner.accounts.views.profile.EditProfileView.update_klant_via_esuite"
    )
    def test_image_is_saved_when_begeleider_and_digid_login(self, mock_update):
        mock_update.return_value = True

        self.user.contact_type = ContactTypeChoices.begeleider
        self.user.login_type = LoginTypeChoices.digid
        self.user.save()

        img_bytes = create_image_bytes()
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

    # -------------------------------------------------------------------------
    # eSuite API sync
    # -------------------------------------------------------------------------

    @requests_mock.Mocker()
    def test_eherkenning_user_updates_klant_api(self, m):
        MockAPIReadPatchData.setUpServices()

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                with requests_mock.Mocker() as m:
                    eherkenning_kvk = (
                        f"0000000{int(use_rsin_for_innNnpId_query_parameter)}"
                    )
                    data = MockAPIReadPatchData(
                        eherkenning_kvk=eherkenning_kvk
                    ).install_mocks_eherkenning(
                        m, use_rsin=use_rsin_for_innNnpId_query_parameter
                    )
                    config = ESuiteKlantConfig.get_solo()
                    config.use_rsin_for_innNnpId_query_parameter = (
                        use_rsin_for_innNnpId_query_parameter
                    )
                    config.save()

                    response = self.app.get(self.url, user=data.eherkenning_user)
                    m.reset_mock()
                    self.clearTimelineLogs()

                    form = response.forms["profile-edit"]
                    form["email_addresses-0-value"] = "new@example.com"
                    form["email_addresses-0-is_standard_for_type"] = True
                    form.submit()

                    self.assertTrue(data.matchers[0].called)
                    klant_patch_data = data.matchers[1].request_history[0].json()
                    self.assertEqual(
                        klant_patch_data,
                        {
                            "emailadres": "new@example.com",
                        },
                    )
                    self.assertTimelineLog("retrieved klant for user")
                    self.assertTimelineLog(
                        "patched klant from user profile edit with fields: emailadres"
                    )

    @requests_mock.Mocker()
    def test_no_edited_fields_does_not_push_to_esuite(self, m):
        MockAPIReadPatchData.setUpServices()
        data = MockAPIReadPatchData().install_mocks(m)

        response = self.app.get(self.url, user=data.user)
        m.reset_mock()
        self.clearTimelineLogs()

        form = response.forms["profile-edit"]
        form.submit()

        self.assertFalse(data.matchers[0].called)
        self.assertFalse(data.matchers[1].called)

    @requests_mock.Mocker()
    def test_modify_phone_and_email_updates_klant_api(self, m):
        MockAPIReadPatchData.setUpServices()
        data = MockAPIReadPatchData().install_mocks(m)

        self.client.force_login(data.user)
        m.reset_mock()
        self.clearTimelineLogs()

        post_data = {}
        post_data.update(
            self._da_formset_data("email_addresses", [("new@example.com", True)])
        )
        post_data.update(
            self._da_formset_data(
                "phone_addresses",
                [("0612345678", True), ("0687654321", False)],
            )
        )
        self.client.post(self.url, data=post_data)

        self.assertTrue(data.matchers[0].called)
        klant_patch_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            klant_patch_data,
            {
                "emailadres": "new@example.com",
                "telefoonnummer": "0612345678",
                "telefoonnummerAlternatief": "0687654321",
            },
        )
        self.assertTimelineLog("retrieved klant for user")
        self.assertTimelineLog(
            "patched klant from user profile edit with fields: emailadres, telefoonnummer, telefoonnummerAlternatief"
        )

    @requests_mock.Mocker()
    def test_modify_phone_updates_klant_api_but_skip_unchanged_email(self, m):
        MockAPIReadPatchData.setUpServices()
        data = MockAPIReadPatchData().install_mocks(m)

        response = self.app.get(self.url, user=data.user)
        m.reset_mock()
        self.clearTimelineLogs()

        form = response.forms["profile-edit"]
        form["phone_addresses-0-value"] = "0612345678"
        form["phone_addresses-0-is_standard_for_type"] = True
        form.submit()

        self.assertTrue(data.matchers[0].called)
        klant_patch_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            klant_patch_data,
            {
                "telefoonnummer": "0612345678",
            },
        )
        self.assertTimelineLog("retrieved klant for user")
        self.assertTimelineLog(
            "patched klant from user profile edit with fields: telefoonnummer"
        )

    @requests_mock.Mocker()
    def test_modify_email_updates_klant_api_but_skip_unchanged_phone(self, m):
        MockAPIReadPatchData.setUpServices()
        data = MockAPIReadPatchData().install_mocks(m)

        response = self.app.get(self.url, user=data.user)
        m.reset_mock()
        self.clearTimelineLogs()

        form = response.forms["profile-edit"]
        form["email_addresses-0-value"] = "new@example.com"
        form["email_addresses-0-is_standard_for_type"] = True
        form.submit()

        self.assertTrue(data.matchers[0].called)
        klant_patch_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            klant_patch_data,
            {
                "emailadres": "new@example.com",
            },
        )
        self.assertTimelineLog("retrieved klant for user")
        self.assertTimelineLog(
            "patched klant from user profile edit with fields: emailadres"
        )

    # -------------------------------------------------------------------------
    # OpenKlant2 API sync
    # -------------------------------------------------------------------------

    @requests_mock.Mocker()
    def test_update_via_openklant(self, m):
        MockAPIReadPatchData.setUpServices(
            klanten_service_type=KlantenServiceType.OPENKLANT2
        )
        data = MockAPIReadPatchData().install_mocks_openklant(m)

        self.client.force_login(data.digid_user)
        m.reset_mock()
        self.clearTimelineLogs()

        post_data = {}
        post_data.update(
            self._da_formset_data("email_addresses", [("new@example.com", True)])
        )
        post_data.update(
            self._da_formset_data(
                "phone_addresses",
                [("0612345678", True), ("0687654321", False)],
            )
        )
        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 302)

        digitale_adressen_requests = [
            req for req in m.request_history if "digitaleadressen" in req.path
        ]
        email_requests = [
            req
            for req in digitale_adressen_requests
            if req.method == "POST" and req.json().get("soortDigitaalAdres") == "email"
        ]
        self.assertEqual(len(email_requests), 1)
        self.assertEqual(email_requests[0].json()["adres"], "new@example.com")

        phone_requests = [
            req
            for req in digitale_adressen_requests
            if req.method == "POST"
            and req.json().get("soortDigitaalAdres") == "telefoonnummer"
        ]
        self.assertEqual(len(phone_requests), 2)
        phone_numbers = [req.json() for req in phone_requests]
        standard_number = next(n for n in phone_numbers if n["isStandaardAdres"])
        self.assertEqual(standard_number["adres"], "0612345678")
        alt_number = next(n for n in phone_numbers if not n["isStandaardAdres"])
        self.assertEqual(alt_number["adres"], "0687654321")

    @requests_mock.Mocker()
    def test_update_via_openklant_patches_when_mapping_exists(self, m):
        """When a mapping exists, the remote address is PATCHed rather than deleted and recreated."""
        MockAPIReadPatchData.setUpServices(
            klanten_service_type=KlantenServiceType.OPENKLANT2
        )
        data = MockAPIReadPatchData().install_mocks_openklant(m)

        email_addr = DigitalAddressFactory(
            user=data.digid_user,
            type=DigitalAddressType.email,
            value=data.digid_user.email,
            login_type=LoginTypeChoices.digid,
            is_standard_for_type=True,
        )
        REMOTE_UUID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=email_addr, ok_uuid=REMOTE_UUID
        )

        patch_matcher = m.patch(
            f"http://localhost:8338/klantinteracties/api/v1/digitaleadressen/{REMOTE_UUID}",
            json={"uuid": REMOTE_UUID},
        )

        response = self.app.get(self.url, user=data.digid_user)
        m.reset_mock()
        self.clearTimelineLogs()

        form = response.forms["profile-edit"]
        form["email_addresses-0-value"] = "new@example.com"
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(patch_matcher.called)

        delete_requests = [r for r in m.request_history if r.method == "DELETE"]
        self.assertEqual(len(delete_requests), 0)

        post_requests = [
            r
            for r in m.request_history
            if r.method == "POST" and "digitaleadressen" in r.path
        ]
        self.assertEqual(len(post_requests), 0)

    @requests_mock.Mocker()
    def test_delete_with_openklant_mapping_sends_remote_delete(self, m):
        MockAPIReadPatchData.setUpServices(
            klanten_service_type=KlantenServiceType.OPENKLANT2
        )
        data = MockAPIReadPatchData().install_mocks_openklant(m)

        REMOTE_UUID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        email_addr = DigitalAddressFactory(
            user=data.digid_user,
            type=DigitalAddressType.email,
            value=data.digid_user.email,
            login_type=LoginTypeChoices.digid,
            is_standard_for_type=True,
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=email_addr, ok_uuid=REMOTE_UUID
        )
        delete_matcher = m.delete(
            f"http://localhost:8338/klantinteracties/api/v1/digitaleadressen/{REMOTE_UUID}",
            status_code=204,
        )

        self.client.force_login(data.digid_user)

        post_data = self._da_formset_data(
            "email_addresses",
            [(email_addr.value, True)],
            initial_pks=[email_addr.pk],
        )
        post_data["email_addresses-0-DELETE"] = "on"
        post_data.update(self._da_formset_data("phone_addresses", []))

        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(delete_matcher.called)
        self.assertFalse(DigitalAddress.objects.filter(pk=email_addr.pk).exists())

    @requests_mock.Mocker()
    def test_delete_with_openklant_mapping_api_error_rolls_back_local_deletion(self, m):
        MockAPIReadPatchData.setUpServices(
            klanten_service_type=KlantenServiceType.OPENKLANT2
        )
        data = MockAPIReadPatchData().install_mocks_openklant(m)

        REMOTE_UUID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        email_addr = DigitalAddressFactory(
            user=data.digid_user,
            type=DigitalAddressType.email,
            value=data.digid_user.email,
            login_type=LoginTypeChoices.digid,
            is_standard_for_type=True,
        )
        DigitaalAdresOpenKlantMappingFactory(
            digital_address=email_addr, ok_uuid=REMOTE_UUID
        )

        self.client.force_login(data.digid_user)

        post_data = {}
        post_data.update(
            self._da_formset_data(
                "email_addresses",
                [(email_addr.value, True)],
                initial_pks=[email_addr.pk],
            )
        )
        post_data["email_addresses-0-DELETE"] = "on"
        post_data.update(self._da_formset_data("phone_addresses", []))

        with patch(
            "open_inwoner.openklant.services.OpenKlant2Service.delete_remote_digitaal_adressen",
            side_effect=Exception("remote API unavailable"),
        ):
            response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(DigitalAddress.objects.filter(pk=email_addr.pk).exists())
        self.assertTrue(
            DigitaalAdresOpenKlantMapping.objects.filter(
                digital_address=email_addr
            ).exists()
        )

    @requests_mock.Mocker()
    def test_delete_without_openklant_mapping_no_remote_delete(self, m):
        MockAPIReadPatchData.setUpServices(
            klanten_service_type=KlantenServiceType.OPENKLANT2
        )
        user = DigidUserFactory()
        email_addr = DigitalAddressFactory(
            user=user,
            type=DigitalAddressType.email,
            value=user.email,
            login_type=LoginTypeChoices.digid,
            is_standard_for_type=True,
        )
        # No DigitaalAdresOpenKlantMapping — nothing to delete remotely.

        self.client.force_login(user)

        post_data = {}
        post_data.update(
            self._da_formset_data(
                "email_addresses",
                [(email_addr.value, True)],
                initial_pks=[email_addr.pk],
            )
        )
        post_data["email_addresses-0-DELETE"] = "on"
        post_data.update(self._da_formset_data("phone_addresses", []))

        response = self.client.post(self.url, data=post_data)

        self.assertEqual(response.status_code, 302)
        delete_requests = [r for r in m.request_history if r.method == "DELETE"]
        self.assertEqual(delete_requests, [])
        self.assertFalse(DigitalAddress.objects.filter(pk=email_addr.pk).exists())


class TestForm(ErrorMessageMixin, forms.Form):
    name = forms.CharField(required=True, label="Naam")
    email = forms.EmailField(required=True, label="E-mailadres")


class ErrorMessageMixinTest(TestCase):
    def test_default_error_messages(self):
        form = TestForm(data={})
        self.assertEqual(
            form.errors["name"],
            [_('Het verplichte veld "Naam" is niet (goed) ingevuld. Vul het veld in.')],
        )
        self.assertEqual(
            form.errors["email"],
            [
                _(
                    'Het verplichte veld "E-mailadres" is niet (goed) ingevuld. Vul het veld in.'
                )
            ],
        )

    def test_custom_error_messages(self):
        custom_messages = {
            "name": {"required": _("Naam is verplicht.")},
            "email": {"required": _("E-mail is verplicht.")},
        }
        form = TestForm(data={}, custom_error_messages=custom_messages)
        self.assertEqual(form.errors["name"], [_("Naam is verplicht.")])
        self.assertEqual(form.errors["email"], [_("E-mail is verplicht.")])


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class ProfileDeleteTest(WebTest):
    csrf_checks = False

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("profile:detail")

    def setUp(self):
        # Pre-create footer static aliases owned by the CMS test user.
        # Without this, {% static_alias %} in master.html creates Version records
        # with created_by=request.user (the test user), and Version.created_by has
        # on_delete=PROTECT, which blocks the user.delete() call under test.
        cms_tools.create_static_aliases(
            ["footer_left", "footer_center", "footer_right"]
        )
        self._infra_user_pks = set(User.objects.values_list("pk", flat=True))

    @property
    def regular_users(self):
        return User.objects.exclude(pk__in=self._infra_user_pks)

    def test_delete_regular_user_success(self):
        user = UserFactory()

        # get profile page
        response = self.app.get(self.url, user=user)

        # check delete
        response = response.forms["delete-form"].submit()
        self.assertIsNone(self.regular_users.first())

        # check redirect directly to login (no longer via logout)
        self.assertRedirects(
            response,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_delete_user_with_digid_login_success(self):
        user = DigidUserFactory()

        # get profile page
        response = self.app.get(self.url, user=user)

        # check user deleted
        response = response.forms["delete-form"].submit()
        self.assertIsNone(self.regular_users.first())

        # check redirect directly to login (no longer via logout)
        self.assertRedirects(
            response,
            reverse("login"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_delete_regular_user_as_plan_contact_fail(self):
        user = UserFactory()
        PlanFactory.create(plan_contacts=[user])

        # get profile page
        response = self.app.get(self.url, user=user)

        # check user not deleted
        response = response.forms["delete-form"].submit()
        self.assertEqual(self.regular_users.first(), user)

        # check redirect
        self.assertRedirects(
            response,
            reverse("profile:detail"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

    def test_delete_staff_user_via_frontend_does_not_work(self):
        user = UserFactory(is_staff=True)

        # get profile page
        response = self.app.get(self.url, user=user)

        # check staff user not deleted
        response = response.forms["delete-form"].submit()
        self.assertEqual(self.regular_users.first(), user)

        # check redirect
        self.assertRedirects(
            response,
            reverse("profile:detail"),
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class MyDataTests(AssertTimelineLogMixin, HaalCentraalMixin, WebTest):
    maxDiff = None

    expected_response = BRPData(
        first_name="Merel",
        initials="M.",
        last_name="Kooyman",
        infix="de",
        birthday=date(1982, 4, 10),
        birth_place="Leerdam",
        gender="vrouw",
        street="King Olivereiland",
        housenumber="64",
        postal_code="2551JV",
        city="'s-Gravenhage",
        country="",
    )

    def setUp(self):
        self.user = UserFactory(
            bsn="999993847",
            first_name="Merel",
            infix="de",
            last_name="Kooyman",
            login_type=LoginTypeChoices.digid,
        )
        self.url = reverse("profile:data")

        self.expected_strings = [
            self.expected_response.first_name,
            self.expected_response.infix,
            self.expected_response.last_name,
            django_date(self.expected_response.birthday, "j F Y"),
            self.expected_response.birth_place,
            self.expected_response.gender,
            self.expected_response.street,
            self.expected_response.get_housenumber(),
            self.expected_response.postal_code,
            self.expected_response.city,
            self.user.bsn,
            self.user.email,
        ]
        self.clearTimelineLogs()

    def assertDataDisplays(self, response):
        texts = set()
        for elem in response.pyquery(".tabled__item:not(.tabled__item--bold)"):
            s = elem.text.strip()
            texts.add(s)

        if missing := [s for s in self.expected_strings if s not in texts]:
            f = ", ".join(f"'{s}'" for s in missing)
            self.fail(f"missing display of values: {f}")

    def test_expected_response_is_returned_brp_v_2(self, m):
        self._setUpMocks_v_2(m)
        self._setUpService()

        response = self.app.get(self.url, user=self.user)
        self.assertEqual(
            asdict(response.context["my_data"]),
            asdict(self.expected_response),
        )
        # self.assertDataDisplays(response)
        self.assertTimelineLog(
            _("user requests for brp data"),
            content_object_repr=str(self.user),
            action_flag=list(LOG_ACTIONS[4]),
        )

    def test_expected_response_is_returned_brp_v_1_3(self, m):
        self._setUpMocks_v_1_3(m)
        self._setUpService()
        self._setUpVersion("1.3")

        response = self.app.get(self.url, user=self.user)
        self.assertEqual(
            asdict(response.context["my_data"]),
            asdict(self.expected_response),
        )
        self.assertDataDisplays(response)
        self.assertTimelineLog(
            _("user requests for brp data"),
            content_object_repr=str(self.user),
            action_flag=list(LOG_ACTIONS[4]),
        )

    def test_wrong_date_format_shows_birthday_none_brp_v_1_3(self, m):
        self._setUpService()
        self._setUpVersion("1.3")

        m.get(
            "https://personen/api/schema/openapi.yaml?v=3",
            status_code=200,
            content=self.load_binary_mock("personen_1.3.yaml"),
        )
        m.get(
            "https://personen/api/brp/ingeschrevenpersonen/999993847?fields=geslachtsaanduiding,naam.voornamen,naam.geslachtsnaam,naam.voorletters,naam.voorvoegsel,verblijfplaats.straat,verblijfplaats.huisletter,verblijfplaats.huisnummertoevoeging,verblijfplaats.woonplaats,verblijfplaats.postcode,verblijfplaats.land.omschrijving,geboorte.datum.datum,geboorte.plaats.omschrijving",
            status_code=200,
            json={
                "naam": {
                    "voornamen": "Merel",
                    "voorvoegsel": "de",
                    "geslachtsnaam": "Kooyman",
                },
                "geboorte": {
                    "datum": {
                        "datum": "1982-04",
                    },
                },
            },
        )
        response = self.app.get(self.url, user=self.user)

        self.assertIsNone(response.context["my_data"].birthday)
        self.assertTimelineLog(
            _("user requests for brp data"),
            content_object_repr=str(self.user),
            action_flag=list(LOG_ACTIONS[4]),
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
@patch("open_inwoner.cms.utils.page_display._is_published", return_value=True)
class EditNotificationsTests(AssertTimelineLogMixin, WebTest):
    def setUp(self):
        self.config = SiteConfiguration.get_solo()
        self.config.notifications_messages_enabled = True
        self.config.notifications_cases_enabled = True
        self.config.notifications_plans_enabled = True
        self.config.save()

        self.url = reverse("profile:notifications")
        self.user = UserFactory()

    def test_login_required(self, mock_page_display):
        login_url = reverse("login")
        response = self.app.get(self.url)

        self.assertRedirects(response, f"{login_url}?next={self.url}")

    def test_notifications_disabled(self, mock_page_display):
        self.config.notifications_actions_enabled = False
        self.config.notifications_cases_enabled = False
        self.config.notifications_messages_enabled = False
        self.config.notifications_plans_enabled = False
        self.config.save()

        response = self.app.get(self.url, user=self.user)

        self.assertRedirects(response, reverse("profile:detail"))

    def test_default_values_for_regular_user(self, mock_page_display):
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertTrue(form.get("messages_notifications").checked)
        self.assertTrue(form.get("plans_notifications").checked)
        self.assertNotIn("cases_notifications", form.fields)

    def test_disabling_notification_is_saved(self, mock_page_display):
        self.assertTrue(self.user.messages_notifications)

        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]
        form["messages_notifications"] = False
        form.submit()

        self.user.refresh_from_db()

        self.assertTrue(self.user.cases_notifications)
        self.assertFalse(self.user.messages_notifications)
        self.assertTrue(self.user.plans_notifications)
        self.assertEqual(
            self.user.case_notification_channel,
            NotificationChannelChoice.digital_and_post,
        )

    def test_cases_notifications_is_accessible_when_digid_user(self, mock_page_display):
        self.user.login_type = LoginTypeChoices.digid
        self.user.save()
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertIn("cases_notifications", form.fields)

    def test_notification_channel_not_accessible_when_disabled(self, mock_page_display):
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        # choice of notification channel is disabled by default
        self.assertNotIn("case_notification_channel_choice", form.fields)

    @requests_mock.Mocker()
    def test_notification_channel_edit(self, mock_page_display, m):
        MockAPIReadPatchData.setUpServices()
        data = MockAPIReadPatchData().install_mocks(m)

        config = SiteConfiguration.get_solo()
        config.notifications_cases_enabled = True
        config.enable_notification_channel_choice = True
        config.save()

        # reset noise from signals
        m.reset_mock()
        self.clearTimelineLogs()

        self.user.bsn = data.user.bsn
        self.user.save()

        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]
        form["case_notification_channel"] = NotificationChannelChoice.digital_only
        form.submit()

        # check user
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.case_notification_channel, NotificationChannelChoice.digital_only
        )

        # check klant api update
        self.assertTrue(data.matchers[0].called)
        klant_patch_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            klant_patch_data,
            {
                "toestemmingZaakNotificatiesAlleenDigitaal": True,
            },
        )
        self.assertTimelineLog("retrieved klant for user")
        self.assertTimelineLog(
            "patched klant from user profile edit with fields: toestemmingZaakNotificatiesAlleenDigitaal"
        )


@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class NotificationsDisplayTests(WebTest):
    """Integration tests for display of notifications and publication of CMS pages"""

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse("profile:notifications")
        cls.user = UserFactory()

        config = SiteConfiguration.get_solo()
        config.notifications_messages_enabled = True
        config.notifications_cases_enabled = True
        config.notifications_plans_enabled = True
        config.save()

    def test_inbox_notifications_display(self):
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertNotIn("messages_notifications", form.fields)

        # inbox page created but not published
        page = cms_tools.create_apphook_page(InboxApphook, publish=False)

        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertNotIn("messages_notifications", form.fields)

        # inbox page published
        cms_tools.publish_page(page, "nl")
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertIn("messages_notifications", form.fields)

    def test_cases_notifications_display(self):
        # cases page not created
        self.user.login_type = LoginTypeChoices.digid
        self.user.save()
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertNotIn("cases_notifications", form.fields)

        # cases page created but not published
        page = cms_tools.create_apphook_page(CasesApphook, publish=False)
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertNotIn("cases_notifications", form.fields)

        # cases page published
        cms_tools.publish_page(page, "nl")
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertIn("cases_notifications", form.fields)

    def test_collaborate_notifications_display(self):
        # collaborate page not created
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertNotIn("plans_notifications", form.fields)

        # collaborate page created but not published
        page = cms_tools.create_apphook_page(CollaborateApphook, publish=False)

        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertNotIn("plans_notifications", form.fields)

        # collaborate page published
        cms_tools.publish_page(page, "nl")
        response = self.app.get(self.url, user=self.user)
        form = response.forms["change-notifications"]

        self.assertIn("plans_notifications", form.fields)


@tag("laposta")
@requests_mock.Mocker()
@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls", MIDDLEWARE=PATCHED_MIDDLEWARE
)
class NewsletterSubscriptionTests(ClearCachesMixin, WebTest):
    def setUp(self):
        super().setUp()

        self.profile_app = ProfileConfig.objects.create(
            namespace=ProfileApphook.app_name, newsletters=True
        )
        cms_tools.create_apphook_page(ProfileApphook)

        self.profile_url = reverse("profile:detail")
        self.user = DigidUserFactory(
            email="news@example.com", verified_email="news@example.com"
        )
        self.assertTrue(self.user.has_verified_email())

        self.config = LapostaConfig.get_solo()
        self.config.api_root = "https://laposta.local/api/v2/"
        self.config.basic_auth_username = "username"
        self.config.basic_auth_password = "password"
        self.config.save()

        self.list1 = LapostaListFactory.build(
            list_id="list1", name="Nieuwsbrief1", remarks="foo"
        )
        self.list2 = LapostaListFactory.build(
            list_id="list2", name="Nieuwsbrief2", remarks="bar"
        )

    def setUpMocks(self, m):
        m.get(
            "https://laposta.local/api/v2/list",
            json={
                "data": [
                    {"list": self.list1.model_dump()},
                    {"list": self.list2.model_dump()},
                ]
            },
        )

    def test_do_not_render_form_if_config_is_missing(self, m):
        self.config.api_root = ""
        self.config.save()

        response = self.app.get(self.profile_url, user=self.user)

        self.assertNotIn("newsletter-form", response.forms)

    def test_do_not_render_form_if_no_newsletters_are_found(self, m):
        m.get("https://laposta.local/api/v2/list", json=[])

        response = self.app.get(self.profile_url, user=self.user)

        self.assertNotIn("newsletter-form", response.forms)

    def test_render_form_if_newsletters_are_found(self, m):
        self.setUpMocks(m)

        self.config.limit_list_selection_to = ["list1", "list2"]
        self.config.save()

        m.get(
            f"{self.config.api_root}member/{self.user.email}?list_id=list1",
            json={
                "member": MemberFactory.build(
                    list_id="list1",
                    member_id="1234567",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )
        m.get(
            f"{self.config.api_root}member/{self.user.email}?list_id=list2",
            status_code=400,
        )

        response = self.app.get(self.profile_url, user=self.user)

        self.assertIn(_("Nieuwsbrieven"), response.text)
        self.assertIn("newsletter-form", response.forms)

        form = response.forms["newsletter-form"]

        # First checkbox should be checked, because the user is already subscribed
        self.assertTrue(form.fields["newsletters"][0].checked)
        self.assertFalse(form.fields["newsletters"][1].checked)
        self.assertIn("Nieuwsbrief1", response.text)
        self.assertIn("Nieuwsbrief2", response.text)

    def test_save_form_with_errors(self, m):
        self.setUpMocks(m)

        self.config.limit_list_selection_to = ["list1", "list2"]
        self.config.save()

        m.get(
            f"{self.config.api_root}member/{self.user.email}?list_id=list1",
            json={
                "member": MemberFactory.build(
                    list_id="list1",
                    member_id="1234567",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )
        m.get(
            f"{self.config.api_root}member/{self.user.email}?list_id=list2",
            status_code=400,
        )

        response = self.app.get(self.profile_url, user=self.user)

        self.assertIn(_("Nieuwsbrieven"), response.text)
        self.assertIn("newsletter-form", response.forms)

        form = response.forms["newsletter-form"]

        # First checkbox should be checked, because the user is already subscribed
        self.assertTrue(form.fields["newsletters"][0].checked)
        self.assertIn("Nieuwsbrief1", response.text)

        post_matcher = m.post(
            f"{self.config.api_root}member",
            json={
                "error": {
                    "type": "internal",
                    "message": "Internal server error",
                }
            },
            status_code=500,
        )
        delete_matcher = m.delete(
            f"{self.config.api_root}member/{self.user.email}?list_id=list1",
            json={
                "error": {
                    "type": "internal",
                    "message": "Internal server error",
                }
            },
            status_code=500,
        )

        form["newsletters"] = ["list2"]
        response = form.submit("newsletter-submit")

        subscribe_error, unsubscribe_error = response.pyquery(
            ".notifications__errors .notification__content"
        )

        self.assertEqual(
            PyQuery(subscribe_error).text(),
            _(
                "Something went wrong while trying to subscribe to '{list_name}', please try again later"
            ).format(list_name="Nieuwsbrief2"),
        )
        self.assertEqual(
            PyQuery(unsubscribe_error).text(),
            _(
                "Something went wrong while trying to unsubscribe from '{list_name}', please try again later"
            ).format(list_name="Nieuwsbrief1"),
        )

        form = response.forms["newsletter-form"]

        # The initial data should be kept the same as the last POST
        self.assertFalse(form.fields["newsletters"][0].checked)
        self.assertTrue(form.fields["newsletters"][1].checked)

    def test_do_not_render_form_if_email_not_verified(self, m):
        self.setUpMocks(m)

        self.user.verified_email = ""
        self.user.save()
        self.assertFalse(self.user.has_verified_email())

        self.config.limit_list_selection_to = ["list1"]
        self.config.save()

        m.get(
            f"{self.config.api_root}member/{self.user.email}?list_id=list1",
            json={
                "member": MemberFactory.build(
                    list_id="list1",
                    member_id="1234567",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )
        response = self.app.get(self.profile_url, user=self.user)

        self.assertNotIn("newsletter-form", response.forms)

    def test_render_form_limit_newsletters_to_admin_selection(self, m):
        self.setUpMocks(m)

        self.config.limit_list_selection_to = ["list1"]
        self.config.save()

        m.get(
            f"{self.config.api_root}member/{self.user.email}?list_id=list1",
            json={
                "member": MemberFactory.build(
                    list_id="list1",
                    member_id="1234567",
                    email=self.user.email,
                    custom_fields=None,
                ).model_dump()
            },
        )
        m.get(
            f"{self.config.api_root}member/{self.user.email}?list_id=list2",
            status_code=400,
        )

        response = self.app.get(self.profile_url, user=self.user)

        self.assertIn(_("Nieuwsbrieven"), response.text)
        self.assertIn("newsletter-form", response.forms)

        form = response.forms["newsletter-form"]

        # First checkbox should be checked, because the user is already subscribed
        self.assertTrue(form.fields["newsletters"][0].checked)
        self.assertIn("Nieuwsbrief1", response.text)

        # Second field was excluded by `LapostaConfig.limit_list_selection_to`
        self.assertNotIn("Nieuwsbrief2", response.text)


@tag("qmatic")
@requests_mock.Mocker()
@override_settings(
    ROOT_URLCONF="open_inwoner.cms.tests.urls", MIDDLEWARE=PATCHED_MIDDLEWARE
)
class UserAppointmentsTests(ClearCachesMixin, WebTest):
    appointments_url = reverse_lazy("profile:appointments")

    def setUp(self):
        super().setUp()

        self.data = QmaticMockData()
        self.assertTrue(self.data.user.has_verified_email())

    def test_do_not_render_list_if_config_is_missing(self, m):
        self.data.config.service = None
        self.data.config.save()

        response = self.app.get(self.appointments_url, user=self.data.user)

        self.assertIn(_("Geen afspraken beschikbaar"), response.text)

    def test_do_not_render_list_if_no_customer_is_found(self, m):
        m.get(
            f"{self.data.api_root}appointment/customers/identify;{self.data.user.email}",
            json=[],
        )

        response = self.app.get(self.appointments_url, user=self.data.user)

        self.assertIn(_("Geen afspraken beschikbaar"), response.text)

    def test_do_not_render_list_if_no_appointments_are_found(self, m):
        m.get(
            f"{self.data.api_root}appointment/customers/identify;{self.data.user.email}",
            json=[{"publicId": self.data.public_id}],
        )
        m.get(
            f"{self.data.api_root}calendar-backend/public/api/v1/customers/{self.data.public_id}/appointments",
            status_code=404,
        )

        response = self.app.get(self.appointments_url, user=self.data.user)

        self.assertIn(_("Geen afspraken beschikbaar"), response.text)

    def test_do_not_render_list_if_validation_error(self, m):
        m.get(
            f"{self.data.api_root}appointment/customers/identify;{self.data.user.email}",
            json=[{"publicId": self.data.public_id}],
        )
        m.get(
            f"{self.data.api_root}calendar-backend/public/api/v1/customers/{self.data.public_id}/appointments",
            json={"appointmentList": [{"invalid": "data"}]},
        )

        response = self.app.get(self.appointments_url, user=self.data.user)

        self.assertIn(_("Geen afspraken beschikbaar"), response.text)

    def test_do_not_render_list_if_email_not_verified(self, m):
        self.data.user.verified_email = ""
        self.data.user.save()
        self.assertFalse(self.data.user.has_verified_email())

        response = self.app.get(self.appointments_url, user=self.data.user)

        self.assertIn(_("Geen afspraken beschikbaar"), response.text)

    def test_render_list_if_appointments_are_found(self, m):
        self.data.setUpMocks(m)

        with freeze_time("2020-01-01 00:00"):
            response = self.app.get(self.appointments_url, user=self.data.user)

        self.assertIn(_("Een overzicht van uw afspraken"), response.text)

        cards = response.pyquery(".appointment-info")

        self.assertEqual(len(cards), 2)

        self.assertNotIn("Old appointment", response.text)

        self.assertEqual(PyQuery(cards[0]).find(".card__heading-2").text(), "Paspoort")

        passport_appointment = PyQuery(cards[0]).find("ul").children()

        self.assertEqual(
            PyQuery(passport_appointment[0]).text(), "Datum\n1 januari 2020"
        )
        self.assertEqual(PyQuery(passport_appointment[1]).text(), "Tijd\n13:00 uur")
        self.assertEqual(
            PyQuery(passport_appointment[2]).text(), "Locatie\nHoofdkantoor"
        )
        self.assertEqual(PyQuery(passport_appointment[3]).text(), "Dam 1")
        self.assertEqual(PyQuery(passport_appointment[4]).text(), "1234 ZZ Amsterdam")
        self.assertEqual(
            PyQuery(cards[0]).find("a").attr("href"),
            f"{self.data.config.booking_base_url}{self.data.appointment_passport.publicId}",
        )

        self.assertEqual(PyQuery(cards[1]).find(".card__heading-2").text(), "ID kaart")

        id_card_appointment = PyQuery(cards[1]).find("ul").children()

        self.assertEqual(PyQuery(id_card_appointment[0]).text(), "Datum\n6 maart 2020")
        self.assertEqual(PyQuery(id_card_appointment[1]).text(), "Tijd\n11:30 uur")
        self.assertEqual(
            PyQuery(id_card_appointment[2]).text(), "Locatie\nHoofdkantoor"
        )
        self.assertEqual(PyQuery(id_card_appointment[3]).text(), "Wall Street 1")
        self.assertEqual(PyQuery(id_card_appointment[4]).text(), "1111 AA New York")
        self.assertEqual(
            PyQuery(cards[1]).find("a").attr("href"),
            f"{self.data.config.booking_base_url}{self.data.appointment_idcard.publicId}",
        )
