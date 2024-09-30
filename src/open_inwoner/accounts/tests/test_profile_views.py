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
from pyquery import PyQuery as PQ
from webtest import Upload

from open_inwoner.accounts.choices import NotificationChannelChoice, StatusChoices
from open_inwoner.cms.profile.cms_appconfig import ProfileConfig
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.haalcentraal.tests.mixins import HaalCentraalMixin
from open_inwoner.laposta.models import LapostaConfig
from open_inwoner.laposta.tests.factories import LapostaListFactory, MemberFactory
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.pdc.tests.factories import CategoryFactory
from open_inwoner.plans.tests.factories import PlanFactory
from open_inwoner.qmatic.tests.data import QmaticMockData
from open_inwoner.utils.forms import ErrorMessageMixin
from open_inwoner.utils.logentry import LOG_ACTIONS
from open_inwoner.utils.test import ClearCachesMixin
from open_inwoner.utils.tests.helpers import AssertTimelineLogMixin, create_image_bytes

from ...cms.cases.cms_apps import CasesApphook
from ...cms.collaborate.cms_apps import CollaborateApphook
from ...cms.inbox.cms_apps import InboxApphook
from ...cms.profile.cms_apps import ProfileApphook
from ...cms.tests import cms_tools
from ...haalcentraal.api_models import BRPData
from ...openklant.tests.data import MockAPIReadPatchData
from ...questionnaire.tests.factories import QuestionnaireStepFactory
from ..choices import ContactTypeChoices, LoginTypeChoices
from ..forms import BrpUserForm, UserForm
from ..models import User
from .factories import (
    ActionFactory,
    DigidUserFactory,
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
        self.return_url = reverse("logout")
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

    def test_show_correct_logout_button_for_login_type_default(self):
        response = self.app.get(self.url, user=self.user)

        logout_title = _("Logout")
        logout_link = response.pyquery.find(f"[title='{logout_title}']")

        self.assertEqual(logout_link.attr("href"), reverse("logout"))

    @patch("digid_eherkenning_oidc_generics.models.OpenIDConnectDigiDConfig.get_solo")
    def test_show_correct_logout_button_for_login_type_digid(self, mock_solo):
        for oidc_enabled in [True, False]:
            with self.subTest(oidc_enabled=oidc_enabled):
                mock_solo.return_value.enabled = oidc_enabled

                logout_url = (
                    reverse("digid_oidc:logout")
                    if oidc_enabled
                    else reverse("digid:logout")
                )

                response = self.app.get(self.url, user=self.digid_user)

                logout_title = _("Logout")
                logout_link = response.pyquery.find(f"[title='{logout_title}']")

                self.assertEqual(logout_link.attr("href"), logout_url)

    @patch(
        "digid_eherkenning_oidc_generics.models.OpenIDConnectEHerkenningConfig.get_solo"
    )
    def test_show_correct_logout_button_for_login_type_eherkenning(self, mock_solo):
        for oidc_enabled in [True, False]:
            with self.subTest(oidc_enabled=oidc_enabled):
                mock_solo.return_value.enabled = oidc_enabled

                logout_url = (
                    reverse("eherkenning_oidc:logout")
                    if oidc_enabled
                    else reverse("logout")
                )

                response = self.app.get(self.url, user=self.eherkenning_user)

                logout_title = _("Logout")
                logout_link = response.pyquery.find(f"[title='{logout_title}']")

                self.assertEqual(logout_link.attr("href"), logout_url)

    @patch(
        "open_inwoner.cms.utils.page_display.inbox_page_is_published", return_value=True
    )
    def test_user_information_profile_page(self, m):
        response = self.app.get(self.url, user=self.user)

        self.assertContains(response, self.user.first_name)
        self.assertContains(response, f"Welkom, {self.user.display_name}")
        self.assertContains(response, f"{self.user.infix} {self.user.last_name}")
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.phonenumber)
        self.assertContains(response, self.user.street)
        self.assertContains(response, self.user.housenumber)
        self.assertContains(response, self.user.city)

        # check business profile section not displayed
        self.assertNotContains(response, "Bedrijfsgegevens")

        # check notification preferences displayed
        doc = PQ(response.content)

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

        doc = PQ(response.content)

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

        doc = PQ(response.content)

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
        page.publish("nl")
        page.save()

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
        self.eherkenning_user = eHerkenningUserFactory()

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
        self.assertEqual(response.status_code, 200)
        form = response.forms["profile-edit"]
        base_response = form.submit()
        self.assertEqual(base_response.url, self.return_url)
        followed_response = base_response.follow()
        self.assertEqual(followed_response.status_code, 200)

    def test_save_empty_form_fails(self):
        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]
        form["first_name"] = ""
        form["last_name"] = ""
        form["email"] = ""
        form["phonenumber"] = ""
        form["street"] = ""
        form["housenumber"] = ""
        form["postcode"] = ""
        form["city"] = ""
        base_response = form.submit()
        expected_errors = {
            "email": [
                _(
                    'Het verplichte veld "E-mailadres" is niet (goed) ingevuld. Vul het veld in.'
                )
            ]
        }
        self.assertEqual(base_response.context["form"].errors, expected_errors)

    def test_save_filled_form(self):
        response = self.app.get(self.url, user=self.user, status=200)
        form = response.forms["profile-edit"]
        form["first_name"] = "First name"
        form["last_name"] = "Last name"
        form["email"] = "user@example.com"
        form["phonenumber"] = "0612345678"
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
        self.assertEqual(self.user.street, "Keizersgracht")
        self.assertEqual(self.user.housenumber, "17 d")
        self.assertEqual(self.user.postcode, "1013 RM")
        self.assertEqual(self.user.city, "Amsterdam")

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

    def test_modify_email_succeeds(self):
        response = self.app.get(self.url, user=self.user)
        form = response.forms["profile-edit"]
        form["email"] = "user@example.com"
        response = form.submit()
        self.user.refresh_from_db()
        self.assertEqual(response.url, self.return_url)
        self.assertEqual(self.user.email, "user@example.com")

    def test_modify_contact_details_eherkenning_succeeds(self):
        response = self.app.get(self.url, user=self.eherkenning_user)
        form = response.forms["profile-edit"]
        form["email"] = "user@example.com"
        form["phonenumber"] = "0612345678"
        response = form.submit()
        self.eherkenning_user.refresh_from_db()
        self.assertEqual(response.url, self.return_url)
        self.assertEqual(self.eherkenning_user.email, "user@example.com")
        self.assertEqual(self.eherkenning_user.phonenumber, "0612345678")

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

        # check that first_name field is not rendered for digid_brp_user
        with self.assertRaises(AssertionError):
            form["first_name"] = "test"

        form["email"] = "user@example.com"
        form["phonenumber"] = "0612345678"
        response = form.submit()

        self.assertEqual(response.url, self.return_url)

        user.refresh_from_db()

        self.assertEqual(user.display_name, "name")
        self.assertEqual(user.email, "user@example.com")
        self.assertEqual(user.phonenumber, "0612345678")

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

        img_bytes = create_image_bytes()
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

    @requests_mock.Mocker()
    def test_modify_phone_and_email_updates_klant_api(self, m):
        MockAPIReadPatchData.setUpServices()
        data = MockAPIReadPatchData().install_mocks(m)

        response = self.app.get(self.url, user=data.user)

        # reset noise from signals
        m.reset_mock()
        self.clearTimelineLogs()

        form = response.forms["profile-edit"]
        form["email"] = "new@example.com"
        form["phonenumber"] = "0612345678"
        form.submit()

        # user data tested in other cases

        self.assertTrue(data.matchers[0].called)
        klant_patch_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            klant_patch_data,
            {
                "emailadres": "new@example.com",
                "telefoonnummer": "0612345678",
            },
        )
        self.assertTimelineLog("retrieved klant for user")
        self.assertTimelineLog(
            "patched klant from user profile edit with fields: emailadres, telefoonnummer"
        )

    @requests_mock.Mocker()
    def test_eherkenning_user_updates_klant_api(self, m):
        MockAPIReadPatchData.setUpServices()

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                # NOTE Explicitly creating a new Mocker object here, because for some reason
                # `m` is overridden somewhere, which causes issues when `MockAPIReadPatchData.install_mocks`
                # is run for the second time
                with requests_mock.Mocker() as m:
                    data = MockAPIReadPatchData().install_mocks_eherkenning(
                        m, use_rsin=use_rsin_for_innNnpId_query_parameter
                    )

                    config = OpenKlantConfig.get_solo()
                    config.use_rsin_for_innNnpId_query_parameter = (
                        use_rsin_for_innNnpId_query_parameter
                    )
                    config.save()

                    response = self.app.get(self.url, user=data.eherkenning_user)

                    # reset noise from signals
                    m.reset_mock()
                    self.clearTimelineLogs()

                    form = response.forms["profile-edit"]
                    form["email"] = "new@example.com"
                    form["phonenumber"] = "0612345678"
                    form.submit()

                    # user data tested in other cases
                    self.assertTrue(data.matchers[0].called)
                    klant_patch_data = data.matchers[1].request_history[0].json()
                    self.assertEqual(
                        klant_patch_data,
                        {
                            "emailadres": "new@example.com",
                            "telefoonnummer": "0612345678",
                        },
                    )
                    self.assertTimelineLog("retrieved klant for user")
                    self.assertTimelineLog(
                        "patched klant from user profile edit with fields: emailadres, telefoonnummer"
                    )

    @requests_mock.Mocker()
    def test_modify_phone_updates_klant_api_but_skips_unchanged(self, m):
        MockAPIReadPatchData.setUpServices()
        data = MockAPIReadPatchData().install_mocks(m)

        response = self.app.get(self.url, user=data.user)

        # reset noise from signals
        m.reset_mock()
        self.clearTimelineLogs()

        form = response.forms["profile-edit"]
        form.submit()

        # user data tested in other cases

        self.assertFalse(data.matchers[0].called)
        self.assertFalse(data.matchers[1].called)

    @requests_mock.Mocker()
    def test_modify_phone_updates_klant_api_but_skip_unchanged_email(self, m):
        MockAPIReadPatchData.setUpServices()
        data = MockAPIReadPatchData().install_mocks(m)

        response = self.app.get(self.url, user=data.user)

        # reset noise from signals
        m.reset_mock()
        self.clearTimelineLogs()

        form = response.forms["profile-edit"]
        form["phonenumber"] = "0612345678"
        form.submit()

        # user data tested in other cases

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

        # reset noise from signals
        m.reset_mock()
        self.clearTimelineLogs()

        form = response.forms["profile-edit"]
        form["email"] = "new@example.com"
        form.submit()

        # user data tested in other cases

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

    def test_delete_regular_user_success(self):
        user = UserFactory()

        # get profile page
        response = self.app.get(self.url, user=user)

        # check delete
        response = response.forms["delete-form"].submit()
        self.assertIsNone(User.objects.first())

        # check redirect
        self.assertRedirects(
            self.app.get(response.url),
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
        self.assertIsNone(User.objects.first())

        # check redirect
        self.assertRedirects(
            self.app.get(response.url),
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
        self.assertEqual(User.objects.first(), user)

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
        self.assertEqual(User.objects.first(), user)

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
            self.user.phonenumber,
        ]
        self.clearTimelineLogs()

    def assertDataDisplays(self, response):
        texts = set()
        for elem in response.pyquery(".tabled__item:not(.tabled__item--bold)"):
            s = elem.text.strip()
            texts.add(s)

        missing = list()
        for s in self.expected_strings:
            if s not in texts:
                missing.append(s)

        if missing:
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

    @override_settings(BRP_VERSION="1.3")
    def test_expected_response_is_returned_brp_v_1_3(self, m):
        self._setUpMocks_v_1_3(m)
        self._setUpService()

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

    @override_settings(BRP_VERSION="1.3")
    def test_wrong_date_format_shows_birthday_none_brp_v_1_3(self, m):
        self._setUpService()

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
        page.publish("nl")
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
        page.publish("nl")
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
        page.publish("nl")
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
            PQ(subscribe_error).text(),
            _(
                "Something went wrong while trying to subscribe to '{list_name}', please try again later"
            ).format(list_name="Nieuwsbrief2"),
        )
        self.assertEqual(
            PQ(unsubscribe_error).text(),
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

        response = self.app.get(self.appointments_url, user=self.data.user)

        self.assertIn(_("Een overzicht van uw afspraken"), response.text)

        cards = response.pyquery(".appointment-info")

        self.assertEqual(len(cards), 2)

        self.assertEqual(PQ(cards[0]).find(".card__heading-2").text(), "Paspoort")

        passport_appointment = PQ(cards[0]).find("ul").children()

        self.assertEqual(PQ(passport_appointment[0]).text(), "Datum\n1 januari 2020")
        self.assertEqual(PQ(passport_appointment[1]).text(), "Tijd\n13:00 uur")
        self.assertEqual(PQ(passport_appointment[2]).text(), "Locatie\nHoofdkantoor")
        self.assertEqual(PQ(passport_appointment[3]).text(), "Dam 1")
        self.assertEqual(PQ(passport_appointment[4]).text(), "1234 ZZ Amsterdam")
        self.assertEqual(
            PQ(cards[0]).find("a").attr("href"),
            f"{self.data.config.booking_base_url}{self.data.appointment_passport.publicId}",
        )

        self.assertEqual(PQ(cards[1]).find(".card__heading-2").text(), "ID kaart")

        id_card_appointment = PQ(cards[1]).find("ul").children()

        self.assertEqual(PQ(id_card_appointment[0]).text(), "Datum\n6 maart 2020")
        self.assertEqual(PQ(id_card_appointment[1]).text(), "Tijd\n11:30 uur")
        self.assertEqual(PQ(id_card_appointment[2]).text(), "Locatie\nHoofdkantoor")
        self.assertEqual(PQ(id_card_appointment[3]).text(), "Wall Street 1")
        self.assertEqual(PQ(id_card_appointment[4]).text(), "1111 AA New York")
        self.assertEqual(
            PQ(cards[1]).find("a").attr("href"),
            f"{self.data.config.booking_base_url}{self.data.appointment_idcard.publicId}",
        )
