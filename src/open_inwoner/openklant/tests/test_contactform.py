import inspect
from unittest.mock import patch

from django.contrib import messages
from django.core import mail
from django.test import modify_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.api_models import KlantContactRol
from open_inwoner.openklant.models import OpenKlantConfig
from open_inwoner.openklant.tests.data import MockAPICreateData
from open_inwoner.openklant.tests.factories import ContactFormSubjectFactory
from open_inwoner.openklant.views.contactform import ContactFormView
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin
from open_inwoner.utils.tests.helpers import AssertFormMixin, AssertTimelineLogMixin


@requests_mock.Mocker()
@modify_settings(
    MIDDLEWARE={"remove": ["open_inwoner.kvk.middleware.KvKLoginMiddleware"]}
)
@patch(
    "open_inwoner.openklant.views.contactform.send_contact_confirmation_mail",
    autospec=True,
)
@patch(
    "open_inwoner.openklant.views.contactform.generate_question_answer_pair",
    autospec=True,
    return_value=("", 42),
)
class ContactFormIntegrationTest(
    ClearCachesMixin,
    AssertTimelineLogMixin,
    AssertFormMixin,
    DisableRequestLogMixin,
    WebTest,
):
    """Integration tests for `ContactForm` and associated view"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = reverse("contactform")

    def setUp(self):
        super().setUp()
        # clear config
        config = OpenKlantConfig.get_solo()
        config.klanten_service = None
        config.contactmomenten_service = None
        config.register_email = ""
        config.register_contact_moment = False
        config.register_bronorganisatie_rsin = ""
        config.register_type = ""
        config.register_employee_id = ""
        config.send_email_confirmation = True
        config.save()

        # bypass CMS for rendering form template directly via ContactFormView
        ContactFormView.template_name = "pages/contactform/form.html"

    def test_singleton_has_configuration_method(
        self, m, mock_captcha, mock_send_confirm
    ):
        # use cleared (from setUp()
        config = OpenKlantConfig.get_solo()
        self.assertFalse(config.has_form_configuration())

        ContactFormSubjectFactory(config=config)

        # email and subject
        config.register_email = "example@example.com"
        self.assertTrue(config.has_form_configuration())

        # subject but nothing else
        config.register_email = ""
        self.assertFalse(config.has_form_configuration())

        # API and subject
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "0123456789"
        config.klanten_service = ServiceFactory()
        config.contactmomenten_service = ServiceFactory()
        config.register_type = "Melding"
        config.register_employee_id = "FooVonBar"
        self.assertTrue(config.has_form_configuration())

        mock_send_confirm.assert_not_called()

    def test_no_form_shown_if_not_has_configuration(
        self, m, mock_captcha, mock_send_confirm
    ):
        # set nothing
        config = OpenKlantConfig.get_solo()
        self.assertFalse(config.has_form_configuration())

        response = self.app.get(self.url)
        self.assertContains(response, _("Contact formulier niet geconfigureerd."))
        self.assertEqual(0, len(response.pyquery("#contactmoment-form")))

    def test_anon_form_requires_either_email_or_phonenumber(
        self, m, mock_captcha, mock_send_confirm
    ):
        config = OpenKlantConfig.get_solo()
        config.register_email = "example@example.com"
        config.save()
        subject = ContactFormSubjectFactory(config=config)

        response = self.app.get(self.url)
        form = response.forms["contactmoment-form"]

        self.assertFormExactFields(
            form,
            (
                "subject",
                "first_name",
                "infix",
                "last_name",
                "email",
                "phonenumber",
                "question",
                "captcha",  # captcha present for anon user
            ),
        )
        form["subject"].select(text=subject.subject)
        form["first_name"] = "Foo"
        form["last_name"] = "Bar"
        form["email"] = ""
        form["phonenumber"] = ""
        form["question"] = "hey!\n\nwaddup?"
        form["captcha"] = 42

        response = form.submit(status=200)
        self.assertEqual(
            response.context["errors"], [_("Vul een e-mailadres of telefoonnummer in.")]
        )
        mock_send_confirm.assert_not_called()

    def test_regular_auth_form_fills_email_and_phonenumber(
        self, m, mock_captcha, mock_send_confirm
    ):
        config = OpenKlantConfig.get_solo()
        config.register_email = "example@example.com"
        config.save()
        subject = ContactFormSubjectFactory(config=config)

        user = UserFactory()

        response = self.app.get(self.url, user=user)
        form = response.forms["contactmoment-form"]
        self.assertFormExactFields(
            form,
            (
                "subject",
                "question",
            ),
        )
        form["subject"].select(text=subject.subject)
        form["question"] = "hey!\n\nwaddup?"

        response = form.submit(status=302)
        mock_send_confirm.assert_called_once_with(user.email, subject.subject)

    def test_expected_ordered_subjects_are_shown(
        self, m, mock_captcha, mock_send_confirm
    ):
        config = OpenKlantConfig.get_solo()
        config.register_email = "example@example.com"
        config.save()
        subject_1 = ContactFormSubjectFactory(config=config)
        subject_2 = ContactFormSubjectFactory(config=config)

        response = self.app.get(self.url)
        form = response.forms["contactmoment-form"]
        sub_options = form["subject"].options

        self.assertEqual(
            sub_options,
            [
                ("", True, _("Selecteren")),
                (str(subject_1.pk), False, subject_1.subject),
                (str(subject_2.pk), False, subject_2.subject),
            ],
        )

        # swap positions and test the updated order
        subject_1.swap(subject_2)

        response = self.app.get(self.url)
        form = response.forms["contactmoment-form"]
        sub_options = form["subject"].options

        self.assertEqual(
            sub_options,
            [
                ("", True, _("Selecteren")),
                (str(subject_2.pk), False, subject_2.subject),
                (str(subject_1.pk), False, subject_1.subject),
            ],
        )
        mock_send_confirm.assert_not_called()

    def test_submit_and_register_via_email(self, m, mock_captcha, mock_send_confirm):
        config = OpenKlantConfig.get_solo()
        config.register_email = "example@example.com"
        config.has_form_configuration = True
        config.save()
        subject = ContactFormSubjectFactory(config=config)

        response = self.app.get(self.url)
        form = response.forms["contactmoment-form"]
        form["subject"].select(text=subject.subject)
        form["first_name"] = "Foo"
        form["infix"] = "de"
        form["last_name"] = "Bar"
        form["email"] = "foo@example.com"
        form["phonenumber"] = "+31612345678"
        form["question"] = "hey!\n\nwaddup?"
        form["captcha"] = 42

        response = form.submit().follow()

        msgs = list(response.context["messages"])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(str(msgs[0]), _("Vraag verstuurd!"))
        self.assertEqual(msgs[0].level, messages.SUCCESS)

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertEqual(
            email.subject, "Contact formulier inzending vanaf Open Inwoner Platform"
        )
        self.assertEqual(email.recipients(), ["example@example.com"])
        self.assertIn("Foo de Bar", email.body)
        self.assertIn("foo@example.com", email.body)
        self.assertIn("+31612345678", email.body)
        self.assertIn("hey!\n\nwaddup?", email.body)

        self.assertTimelineLog("registered contactmoment by email")

        mock_send_confirm.assert_called_once_with("foo@example.com", subject.subject)

    def test_submit_and_register_anon_via_api_with_klant(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        config.register_employee_id = "FooVonBar"
        config.save()

        data = MockAPICreateData()
        data.install_mocks_anon_with_klant(m)

        subject = ContactFormSubjectFactory(
            config=config,
            subject="Aanvraag document",
            subject_code="afdeling-xyz",
        )

        response = self.app.get(self.url)
        form = response.forms["contactmoment-form"]
        form["subject"].select(text=subject.subject)
        form["first_name"] = "Foo"
        form["infix"] = "de"
        form["last_name"] = "Bar"
        form["email"] = "foo@example.com"
        form["phonenumber"] = "+31612345678"
        form["question"] = "hey!\n\nwaddup?"
        form["captcha"] = 42

        response = form.submit().follow()

        msgs = list(response.context["messages"])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(str(msgs[0]), _("Vraag verstuurd!"))
        self.assertEqual(msgs[0].level, messages.SUCCESS)

        self.assertEqual(len(mail.outbox), 0)

        for m in data.matchers:
            self.assertTrue(m.called_once, str(m))

        klant_create_data = data.matchers[0].request_history[0].json()
        self.assertEqual(
            klant_create_data,
            {
                "bronorganisatie": "123456789",
                "voornaam": "Foo",
                "voorvoegselAchternaam": "de",
                "achternaam": "Bar",
                "emailadres": "foo@example.com",
                "telefoonnummer": "+31612345678",
            },
        )
        contactmoment_create_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            contactmoment_create_data,
            {
                "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                "bronorganisatie": "123456789",
                "tekst": "hey!\n\nwaddup?",
                "type": "Melding",
                "kanaal": "contactformulier",
                "onderwerp": "afdeling-xyz",
                "contactgegevens": {
                    "emailadres": "foo@example.com",
                    "telefoonnummer": "+31612345678",
                },
            },
        )
        kcm_create_data = data.matchers[2].request_history[0].json()
        self.assertEqual(
            kcm_create_data,
            {
                "contactmoment": "https://contactmomenten.nl/api/v1/contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
                "klant": "https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "rol": KlantContactRol.BELANGHEBBENDE,
            },
        )
        self.assertTimelineLog("created klant for anonymous user")
        self.assertTimelineLog("registered contactmoment by API")

        mock_send_confirm.assert_called_once_with("foo@example.com", subject.subject)

    def test_submit_and_register_anon_via_api_without_klant(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        config.register_channel = "contactformulier"
        config.register_employee_id = "FooVonBar"
        config.save()

        data = MockAPICreateData()
        data.install_mocks_anon_without_klant(m)

        subject = ContactFormSubjectFactory(
            config=config,
            subject="Aanvraag document",
            subject_code="afdeling-xyz",
        )

        response = self.app.get(self.url)
        form = response.forms["contactmoment-form"]
        form["subject"].select(text=subject.subject)
        form["first_name"] = "Foo"
        form["infix"] = "de"
        form["last_name"] = "Bar"
        form["email"] = "foo@example.com"
        form["phonenumber"] = "+31612345678"
        form["question"] = "hey!\n\nwaddup?"
        form["captcha"] = 42

        response = form.submit().follow()

        msgs = list(response.context["messages"])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(str(msgs[0]), _("Vraag verstuurd!"))
        self.assertEqual(msgs[0].level, messages.SUCCESS)

        self.assertEqual(len(mail.outbox), 0)

        for m in data.matchers:
            self.assertTrue(m.called_once, str(m))

        contactmoment_create_data = data.matchers[1].request_history[0].json()

        text = inspect.cleandoc(
            """
        hey!

        waddup?

        Naam: Foo de Bar
        """
        )

        self.assertEqual(
            contactmoment_create_data,
            {
                "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                "bronorganisatie": "123456789",
                "tekst": text,
                "type": "Melding",
                "kanaal": "contactformulier",
                "onderwerp": "afdeling-xyz",
                "contactgegevens": {
                    "emailadres": "foo@example.com",
                    "telefoonnummer": "+31612345678",
                },
            },
        )
        self.assertTimelineLog(
            "could not retrieve or create klant for user, appended info to message"
        )
        self.assertTimelineLog("registered contactmoment by API")
        mock_send_confirm.assert_called_once_with("foo@example.com", subject.subject)

    @patch("open_inwoner.openklant.forms.generate_question_answer_pair")
    def test_submit_and_register_anon_via_api_without_klant_does_not_send_empty_email_or_telephone(
        self, m, mock_captcha2, mock_captcha, mock_send_confirm
    ):
        # we need to patch the captcha Q&A twice because they are re-generated by the form
        mock_captcha2.return_value = ("", 42)

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        config.register_channel = "contactformulier"
        config.register_employee_id = "FooVonBar"
        config.save()

        MockAPICreateData.setUpServices()
        data = MockAPICreateData()
        data.install_mocks_anon_without_klant(m)

        subject = ContactFormSubjectFactory(
            config=config,
            subject="Aanvraag document",
            subject_code="afdeling-xyz",
        )

        for contact_details in (
            {"phonenumber": "+31612345678", "email": ""},
            {"phonenumber": "", "email": "foo@example.com"},
        ):
            with self.subTest():
                m.reset_mock()
                response = self.app.get(self.url)
                form = response.forms["contactmoment-form"]
                form["subject"].select(text=subject.subject)
                form["first_name"] = "Foo"
                form["infix"] = "de"
                form["last_name"] = "Bar"
                form["question"] = "foobar"
                form["phonenumber"] = contact_details["phonenumber"]
                form["email"] = contact_details["email"]
                form["captcha"] = 42

                response = form.submit().follow()

                contactmoment_create_data = data.matchers[1].request_history[0].json()
                contactgegevens = contactmoment_create_data["contactgegevens"]

                if contact_details["email"]:
                    self.assertEqual(
                        contactgegevens["emailadres"], contact_details["email"]
                    )
                else:
                    self.assertNotIn("emailadres", contactgegevens.keys())

                if contact_details["phonenumber"]:
                    self.assertEqual(
                        contactgegevens["telefoonnummer"],
                        contact_details["phonenumber"],
                    )
                else:
                    self.assertNotIn("telefoonnummer", contactgegevens.keys())

    def test_register_bsn_user_via_api_without_id(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        # empty id should be excluded from contactmoment_create_data
        config.register_employee_id = ""
        config.save()

        data = MockAPICreateData()
        data.install_mocks_digid(m)

        subject = ContactFormSubjectFactory(
            config=config,
            subject="Aanvraag document",
            subject_code="afdeling-xyz",
        )

        response = self.app.get(self.url, user=data.user)

        # reset interference from signals
        self.clearTimelineLogs()
        m.reset_mock()

        form = response.forms["contactmoment-form"]
        self.assertFormExactFields(
            form,
            (
                "subject",
                "question",
            ),
        )
        form["subject"].select(text=subject.subject)
        form["question"] = "Lorem ipsum?"

        response = form.submit().follow()

        contactmoment_create_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            contactmoment_create_data,
            {
                "bronorganisatie": "123456789",
                "tekst": "Lorem ipsum?",
                "type": "Melding",
                "kanaal": "contactformulier",
                "onderwerp": "afdeling-xyz",
            },
        )

    def test_submit_and_register_bsn_user_via_api(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        config.register_employee_id = "FooVonBar"
        config.save()

        data = MockAPICreateData()
        data.install_mocks_digid(m)

        subject = ContactFormSubjectFactory(
            config=config,
            subject="Aanvraag document",
            subject_code="afdeling-xyz",
        )

        response = self.app.get(self.url, user=data.user)

        # reset interference from signals
        self.clearTimelineLogs()
        m.reset_mock()

        form = response.forms["contactmoment-form"]
        self.assertFormExactFields(
            form,
            (
                "subject",
                "question",
            ),
        )
        form["subject"].select(text=subject.subject)
        form["question"] = "hey!\n\nwaddup?"

        response = form.submit().follow()

        msgs = list(response.context["messages"])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(str(msgs[0]), _("Vraag verstuurd!"))
        self.assertEqual(msgs[0].level, messages.SUCCESS)

        self.assertEqual(len(mail.outbox), 0)

        for m in data.matchers:
            self.assertTrue(m.called_once, str(m._url))

        contactmoment_create_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            contactmoment_create_data,
            {
                "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                "bronorganisatie": "123456789",
                "tekst": "hey!\n\nwaddup?",
                "type": "Melding",
                "kanaal": "contactformulier",
                "onderwerp": "afdeling-xyz",
            },
        )
        kcm_create_data = data.matchers[2].request_history[0].json()
        self.assertEqual(
            kcm_create_data,
            {
                "contactmoment": "https://contactmomenten.nl/api/v1/contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
                "klant": "https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "rol": KlantContactRol.BELANGHEBBENDE,
            },
        )

        self.assertTimelineLog("retrieved klant for BSN or KVK user")
        self.assertTimelineLog("registered contactmoment by API")
        mock_send_confirm.assert_called_once_with("foo@example.com", subject.subject)

    def test_submit_and_register_kvk_or_rsin_user_via_api(
        self, _m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        config.register_employee_id = "FooVonBar"
        config.save()

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                # NOTE Explicitly creating a new Mocker object here, because for some reason
                # `m` is overridden somewhere, which causes issues when `MockAPIData.setUpOASMocks`
                # is run for the second time
                with requests_mock.Mocker() as m:
                    config.use_rsin_for_innNnpId_query_parameter = (
                        use_rsin_for_innNnpId_query_parameter
                    )
                    config.save()

                    data = MockAPICreateData()
                    data.install_mocks_eherkenning(
                        m, use_rsin=use_rsin_for_innNnpId_query_parameter
                    )

                    subject = ContactFormSubjectFactory(
                        config=config,
                        subject="Aanvraag document",
                        subject_code="afdeling-xyz",
                    )

                    response = self.app.get(self.url, user=data.eherkenning_user)

                    # reset interference from signals
                    self.clearTimelineLogs()
                    m.reset_mock()

                    form = response.forms["contactmoment-form"]
                    self.assertFormExactFields(
                        form,
                        (
                            "subject",
                            "question",
                        ),
                    )
                    form["subject"].select(text=subject.subject)
                    form["question"] = "hey!\n\nwaddup?"

                    response = form.submit().follow()

                    msgs = list(response.context["messages"])

                    self.assertEqual(len(msgs), 1)
                    self.assertEqual(str(msgs[0]), _("Vraag verstuurd!"))
                    self.assertEqual(msgs[0].level, messages.SUCCESS)

                    self.assertEqual(len(mail.outbox), 0)

                    # Note that WebTest doesn't seem to (properly) clear the
                    # messages after each subTest, causing spurious failures in
                    # the assertions above. Thus, we manually clear the
                    # cookiejar to start the next subTest with a clean messages
                    # state.
                    self.app.cookiejar.clear()

                    for m in data.matchers:
                        self.assertTrue(m.called_once, str(m._url))

                    contactmoment_create_data = (
                        data.matchers[1].request_history[0].json()
                    )
                    self.assertEqual(
                        contactmoment_create_data,
                        {
                            "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                            "bronorganisatie": "123456789",
                            "tekst": "hey!\n\nwaddup?",
                            "type": "Melding",
                            "kanaal": "contactformulier",
                            "onderwerp": "afdeling-xyz",
                        },
                    )
                    kcm_create_data = data.matchers[2].request_history[0].json()
                    self.assertEqual(
                        kcm_create_data,
                        {
                            "contactmoment": "https://contactmomenten.nl/api/v1/contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
                            "klant": "https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                            "rol": KlantContactRol.BELANGHEBBENDE,
                        },
                    )

                    self.assertTimelineLog("retrieved klant for BSN or KVK user")
                    self.assertTimelineLog("registered contactmoment by API")

                    mock_send_confirm.assert_called_once_with(
                        "foo@example.com", subject.subject
                    )
                    mock_send_confirm.reset_mock()

    def test_submit_and_register_bsn_user_via_api_and_update_klant(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        config.register_employee_id = "FooVonBar"
        config.save()

        data = MockAPICreateData()
        data.install_mocks_digid_missing_contact_info(m)

        subject = ContactFormSubjectFactory(
            config=config,
            subject="Aanvraag document",
            subject_code="afdeling-xyz",
        )

        response = self.app.get(self.url, user=data.user)

        # reset interference from signals
        self.clearTimelineLogs()
        m.reset_mock()

        form = response.forms["contactmoment-form"]
        self.assertFormExactFields(
            form,
            (
                "subject",
                "question",
            ),
        )
        form["subject"].select(text=subject.subject)
        form["question"] = "hey!\n\nwaddup?"

        form.submit().follow()
        # response tested in other cases

        for m in data.matchers:
            self.assertTrue(m.called_once, str(m._url))

        klant_patch_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            klant_patch_data,
            {
                "emailadres": data.user.email,
                "telefoonnummer": data.user.phonenumber,
            },
        )

        contactmoment_create_data = data.matchers[2].request_history[0].json()
        self.assertEqual(
            contactmoment_create_data,
            {
                "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                "bronorganisatie": "123456789",
                "tekst": "hey!\n\nwaddup?",
                "type": "Melding",
                "kanaal": "contactformulier",
                "onderwerp": "afdeling-xyz",
            },
        )
        kcm_create_data = data.matchers[3].request_history[0].json()
        self.assertEqual(
            kcm_create_data,
            {
                "contactmoment": "https://contactmomenten.nl/api/v1/contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
                "klant": "https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "rol": KlantContactRol.BELANGHEBBENDE,
            },
        )

        self.assertTimelineLog("retrieved klant for BSN or KVK user")
        self.assertTimelineLog(
            "patched klant from user with missing fields: emailadres, telefoonnummer"
        )
        self.assertTimelineLog("registered contactmoment by API")

        mock_send_confirm.assert_called_once_with(data.user.email, subject.subject)
        mock_send_confirm.reset_mock()

    @patch("open_inwoner.openklant.forms.generate_question_answer_pair")
    def test_submit_and_register_kvk_or_rsin_user_via_api_and_update_klant(
        self, m, mock_captcha2, mock_captcha, mock_send_confirm
    ):
        self.maxDiff = None
        MockAPICreateData.setUpServices()

        # we need to patch the captcha Q&A twice because they are re-generated by the form
        mock_captcha2.return_value = ("", 42)

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        config.register_employee_id = "FooVonBar"
        config.save()

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                # NOTE Explicitly creating a new Mocker object here, because for some reason
                # `m` is overridden somewhere, which causes issues when `MockAPIData.setUpOASMocks`
                # is run for the second time
                with requests_mock.Mocker() as m:
                    config.use_rsin_for_innNnpId_query_parameter = (
                        use_rsin_for_innNnpId_query_parameter
                    )
                    config.save()

                    data = MockAPICreateData()
                    data.install_mocks_eherkenning_missing_contact_info(
                        m, use_rsin=use_rsin_for_innNnpId_query_parameter
                    )

                    subject = ContactFormSubjectFactory(
                        config=config,
                        subject="Aanvraag document",
                        subject_code="afdeling-xyz",
                    )

                    response = self.app.get(self.url, user=data.eherkenning_user)

                    # reset interference from signals
                    self.clearTimelineLogs()
                    m.reset_mock()

                    form = response.forms["contactmoment-form"]
                    self.assertFormExactFields(
                        form,
                        (
                            "subject",
                            "question",
                        ),
                    )
                    form["subject"].select(text=subject.subject)
                    form["question"] = "hey!\n\nwaddup?"

                    form.submit().follow()
                    # response tested in other cases

                    for m in data.matchers:
                        self.assertTrue(m.called_once, str(m._url))

                    klant_patch_data = data.matchers[1].request_history[0].json()
                    self.assertEqual(
                        klant_patch_data,
                        {
                            "emailadres": data.eherkenning_user.email,
                            "telefoonnummer": data.eherkenning_user.phonenumber,
                        },
                    )

                    contactmoment_create_data = (
                        data.matchers[2].request_history[0].json()
                    )
                    self.assertEqual(
                        contactmoment_create_data,
                        {
                            "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                            "bronorganisatie": "123456789",
                            "tekst": "hey!\n\nwaddup?",
                            "type": "Melding",
                            "kanaal": "contactformulier",
                            "onderwerp": "afdeling-xyz",
                        },
                    )
                    kcm_create_data = data.matchers[3].request_history[0].json()
                    self.assertEqual(
                        kcm_create_data,
                        {
                            "contactmoment": "https://contactmomenten.nl/api/v1/contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
                            "klant": "https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                            "rol": KlantContactRol.BELANGHEBBENDE,
                        },
                    )

                    self.assertTimelineLog("retrieved klant for BSN or KVK user")
                    self.assertTimelineLog(
                        "patched klant from user with missing fields: emailadres, telefoonnummer"
                    )
                    self.assertTimelineLog("registered contactmoment by API")

                    mock_send_confirm.assert_called_once_with(
                        data.eherkenning_user.email, subject.subject
                    )
                    mock_send_confirm.reset_mock()

    @patch("open_inwoner.openklant.forms.generate_question_answer_pair")
    def test_send_email_confirmation_is_configurable(
        self, m, mock_captcha2, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        # we need to patch the captcha Q&A twice because they are re-generated by the form
        mock_captcha2.return_value = ("", 42)

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
        config.register_employee_id = "FooVonBar"
        config.save()

        data = MockAPICreateData()
        data.install_mocks_anon_with_klant(m)

        subject = ContactFormSubjectFactory(
            config=config,
            subject="Aanvraag document",
            subject_code="afdeling-xyz",
        )
        for send in [True, False]:
            with self.subTest(send=send):
                config.send_email_confirmation = send
                config.save()

                response = self.app.get(self.url)
                form = response.forms["contactmoment-form"]
                form["subject"].select(text=subject.subject)
                form["first_name"] = "Foo"
                form["infix"] = "de"
                form["last_name"] = "Bar"
                form["email"] = "foo@example.com"
                form["phonenumber"] = "+31612345678"
                form["question"] = "hey!\n\nwaddup?"
                form["captcha"] = 42

                response = form.submit().follow()

                if send:
                    mock_send_confirm.assert_called_once()
                else:
                    mock_send_confirm.assert_not_called()
                mock_send_confirm.reset_mock()
