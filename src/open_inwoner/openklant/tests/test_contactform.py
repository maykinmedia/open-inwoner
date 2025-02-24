from unittest.mock import patch

from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import modify_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.api_models import KlantContactRol
from open_inwoner.openklant.constants import KlantenServiceType
from open_inwoner.openklant.models import (
    ContactFormSubject,
    ESuiteKlantConfig,
    KlantenSysteemConfig,
    OpenKlant2Config,
)
from open_inwoner.openklant.tests.data import MockAPICreateData
from open_inwoner.openklant.tests.factories import (
    ContactFormSubjectFactory,
    OpenKlant2ConfigFactory,
)
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
        # clear esuite_config
        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.klanten_service = None
        esuite_config.contactmomenten_service = None
        esuite_config.register_bronorganisatie_rsin = ""
        esuite_config.register_type = ""
        esuite_config.register_employee_id = ""
        esuite_config.send_email_confirmation = True
        esuite_config.save()

        klant_config = KlantenSysteemConfig.get_solo()
        klant_config.primary_backend = KlantenServiceType.ESUITE.value
        klant_config.register_contact_email = ""
        klant_config.save()

        # bypass CMS for rendering form template directly via ContactFormView
        ContactFormView.template_name = "pages/contactform/form.html"

    def test_contactform_configuration_esuite(self, m, mock_captcha, mock_send_confirm):
        # use cleared (from setUp()
        klant_config = KlantenSysteemConfig.get_solo()
        esuite_config = ESuiteKlantConfig.get_solo()

        self.assertFalse(klant_config.has_contactform_configuration)

        # set email on glogal config and create subject for eSuite backend
        klant_config.register_contact_email = "example@example.com"
        ContactFormSubjectFactory(esuite_config=esuite_config)

        self.assertTrue(klant_config.has_contactform_configuration)

        # subject but nothing else
        klant_config.register_contact_email = ""
        self.assertFalse(klant_config.has_contactform_configuration)

        # API and subject
        esuite_config.register_contact_moment = True
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.klanten_service = ServiceFactory()
        esuite_config.contactmomenten_service = ServiceFactory()
        esuite_config.register_type = "Melding"
        esuite_config.register_employee_id = "FooVonBar"
        esuite_config.save()

        self.assertTrue(klant_config.has_contactform_configuration)

        mock_send_confirm.assert_not_called()

    def test_contactform_configuration_openklant(
        self, m, mock_captcha, mock_send_confirm
    ):
        klant_config = KlantenSysteemConfig.get_solo()
        klant_config.primary_backend = KlantenServiceType.OPENKLANT2.value
        klant_config.save()

        test_cases = [
            ("example@example.com", ServiceFactory(), "esuite-code", False),
            ("example@example.com", ServiceFactory(), None, True),
            ("example@example.com", None, "esuite-code", False),
            ("example@example.com", None, None, True),
            ("", ServiceFactory(), "esuite-code", False),
            ("", ServiceFactory(), None, True),
            ("", None, "esuite-code", False),
            ("", None, None, False),
        ]
        for email, service, esuite_code, result in test_cases:
            with self.subTest(email=email, service=service, esuite_code=esuite_code):
                klant_config.register_contact_email = email
                klant_config.save()

                openklant_config = OpenKlant2Config.get_solo()
                openklant_config.service = service
                openklant_config.save()

                ContactFormSubjectFactory(
                    subject="Aanvraag", esuite_subject_code=esuite_code
                )

                self.assertEqual(klant_config.has_contactform_configuration, result)

                # clear DB for next subtest
                ContactFormSubject.objects.all().delete()

        mock_send_confirm.assert_not_called()

    def test_no_form_shown_if_no_contactform_configuration(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        # set nothing
        anon_user = AnonymousUser()
        klant_config = KlantenSysteemConfig.get_solo()
        self.assertFalse(klant_config.has_contactform_configuration)

        response = self.app.get(self.url)
        self.assertContains(response, _("Contact formulier niet geconfigureerd."))
        self.assertEqual(0, len(response.pyquery("#contactmoment-form")))

    def test_anon_form_requires_either_email_or_phonenumber(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.register_contact_email = "example@example.com"
        config.save()

        config = ESuiteKlantConfig.get_solo()
        subject = ContactFormSubjectFactory(esuite_config=config)

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
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_email = "example@example.com"
        config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        subject = ContactFormSubjectFactory(esuite_config=esuite_config)

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
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_email = "example@example.com"
        config.save()

        config = ESuiteKlantConfig.get_solo()
        subject_1 = ContactFormSubjectFactory(esuite_config=config)
        subject_2 = ContactFormSubjectFactory(esuite_config=config)

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

    def test_register_contactmoment_via_email(self, m, mock_captcha, mock_send_confirm):
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_email = "example@example.com"
        config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        subject = ContactFormSubjectFactory(esuite_config=esuite_config)

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

    def test_register_contactmoment_for_anon_user_via_api_esuite(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_via_api = True
        config.send_email_confirmation = True
        config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.register_type = "Melding"
        esuite_config.register_employee_id = "FooVonBar"
        esuite_config.save()

        data = MockAPICreateData()
        data.install_mocks_anon(m)

        subject = ContactFormSubjectFactory(
            subject="Aanvraag document",
            esuite_subject_code="afdeling-xyz",
            esuite_config=esuite_config,
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

        # check that contactmomenten API but not klanten API is hit for anon user
        self.assertTrue(data.matchers[0].called_once, str(m))
        self.assertFalse(data.matchers[1].called_once, str(m))
        self.assertFalse(data.matchers[2].called_once, str(m))

        contactmoment_create_data = data.matchers[0].request_history[0].json()
        self.assertEqual(
            contactmoment_create_data,
            {
                "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                "bronorganisatie": "123456789",
                "tekst": "hey!\n\nwaddup?\n\nNaam: Foo de Bar",
                "type": "Melding",
                "kanaal": "contactformulier",
                "onderwerp": "afdeling-xyz",
                "contactgegevens": {
                    "emailadres": "foo@example.com",
                    "telefoonnummer": "+31612345678",
                },
            },
        )
        self.assertTimelineLog("registered contactmoment via eSuite")
        mock_send_confirm.assert_called_once_with("foo@example.com", subject.subject)

    def test_register_contactmoment_for_digid_user_via_api_openklant(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()
        data = MockAPICreateData()
        data.install_mocks_openklant(m)

        OpenKlant2ConfigFactory()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.OPENKLANT2.value
        config.register_contact_via_api = True
        config.send_email_confirmation = True
        config.save()

        subject = ContactFormSubjectFactory(
            subject="Aanvraag", esuite_subject_code=None
        )

        response = self.app.get(self.url, user=data.digid_user)
        form = response.forms["contactmoment-form"]
        form["subject"].select(text=subject.subject)
        form["question"] = "What?"

        response = form.submit().follow()

        msgs = list(response.context["messages"])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(str(msgs[0]), _("Vraag verstuurd!"))
        self.assertEqual(msgs[0].level, messages.SUCCESS)

        self.assertEqual(len(mail.outbox), 0)

        self.assertTrue(data.matchers[0].called_once, str(m))
        self.assertTrue(data.matchers[1].called_once, str(m))
        self.assertTrue(data.matchers[2].called_once, str(m))

        log_dump = self.getTimelineLogDump()
        self.assertIn("registered question via OpenKlant", log_dump)
        mock_send_confirm.assert_called_once_with(
            data.digid_user.email, subject.subject
        )

    @patch("open_inwoner.openklant.forms.generate_question_answer_pair")
    def test_register_contactmoment_for_anon_user_via_api_does_not_send_empty_email_or_telephone(
        self, m, mock_captcha2, mock_captcha, mock_send_confirm
    ):
        # we need to patch the captcha Q&A twice because they are re-generated by the form
        mock_captcha2.return_value = ("", 42)

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_via_api = True
        config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.register_type = "Melding"
        esuite_config.register_channel = "contactformulier"
        esuite_config.register_employee_id = "FooVonBar"
        esuite_config.save()

        MockAPICreateData.setUpServices()
        data = MockAPICreateData()
        data.install_mocks_anon_without_klant(m)

        subject = ContactFormSubjectFactory(
            subject="Aanvraag document",
            esuite_subject_code="afdeling-xyz",
            esuite_config=esuite_config,
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

    def test_register_contactmoment_for_bsn_user_via_api(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_via_api = True
        config.send_email_confirmation = True
        config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.register_type = "Melding"
        esuite_config.register_employee_id = "FooVonBar"
        esuite_config.save()

        data = MockAPICreateData()
        data.install_mocks_digid(m)

        subject = ContactFormSubjectFactory(
            subject="Aanvraag document",
            esuite_subject_code="afdeling-xyz",
            esuite_config=esuite_config,
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
                "verzendBevestigingsmail": False,
                "rol": KlantContactRol.BELANGHEBBENDE,
            },
        )

        self.assertTimelineLog("retrieved klant for BSN or KVK user")
        self.assertTimelineLog("registered contactmoment via eSuite")
        mock_send_confirm.assert_called_once_with("foo@example.com", subject.subject)

    def test_register_contactmoment_for_bsn_user_via_api_without_id(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_via_api = True
        config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.register_type = "Melding"
        # empty id should be excluded from contactmoment_create_data
        esuite_config.register_employee_id = ""
        esuite_config.save()

        data = MockAPICreateData()
        data.install_mocks_digid(m)

        subject = ContactFormSubjectFactory(
            subject="Aanvraag document",
            esuite_subject_code="afdeling-xyz",
            esuite_config=esuite_config,
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

    def test_register_contactmoment_for_kvk_or_rsin_user_via_api(
        self, _m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_via_api = True
        config.send_email_confirmation = True
        config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.register_type = "Melding"
        esuite_config.register_employee_id = "FooVonBar"
        esuite_config.save()

        for (
            use_rsin_for_innNnpId_query_parameter,
            send_klantcontact_confirmation_email,
        ) in [(True, False), (True, False)]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter,
            ):
                # NOTE Explicitly creating a new Mocker object here, because for some reason
                # `m` is overridden somewhere, which causes issues when `MockAPIData.setUpOASMocks`
                # is run for the second time
                with requests_mock.Mocker() as m:
                    esuite_config.use_rsin_for_innNnpId_query_parameter = (
                        use_rsin_for_innNnpId_query_parameter
                    )
                    esuite_config.send_klantcontact_confirmation_email = (
                        send_klantcontact_confirmation_email
                    )
                    esuite_config.save()

                    data = MockAPICreateData()
                    data.install_mocks_eherkenning(
                        m, use_rsin=use_rsin_for_innNnpId_query_parameter
                    )

                    subject = ContactFormSubjectFactory(
                        subject="Aanvraag document",
                        esuite_subject_code="afdeling-xyz",
                        esuite_config=esuite_config,
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
                            "verzendBevestigingsmail": send_klantcontact_confirmation_email,
                            "rol": KlantContactRol.BELANGHEBBENDE,
                        },
                    )

                    self.assertTimelineLog("retrieved klant for BSN or KVK user")
                    self.assertTimelineLog("registered contactmoment via eSuite")

                    mock_send_confirm.assert_called_once_with(
                        "foo@example.com", subject.subject
                    )
                    mock_send_confirm.reset_mock()

    def test_register_contactmoment_for_bsn_user_via_api_and_update_klant(
        self, m, mock_captcha, mock_send_confirm
    ):
        MockAPICreateData.setUpServices()

        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = KlantenServiceType.ESUITE.value
        config.register_contact_via_api = True
        config.send_email_confirmation = True
        config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.register_type = "Melding"
        esuite_config.register_employee_id = "FooVonBar"
        esuite_config.save()

        data = MockAPICreateData()
        data.install_mocks_digid_missing_contact_info(m)

        subject = ContactFormSubjectFactory(
            subject="Aanvraag document",
            esuite_subject_code="afdeling-xyz",
            esuite_config=esuite_config,
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
                "verzendBevestigingsmail": False,
                "rol": KlantContactRol.BELANGHEBBENDE,
            },
        )

        self.assertTimelineLog("retrieved klant for BSN or KVK user")
        self.assertTimelineLog(
            "patched klant from user with missing fields: emailadres, telefoonnummer"
        )
        self.assertTimelineLog("registered contactmoment via eSuite")

        mock_send_confirm.assert_called_once_with(data.user.email, subject.subject)
        mock_send_confirm.reset_mock()

    @patch("open_inwoner.openklant.forms.generate_question_answer_pair")
    def test_register_contactmoment_for_kvk_or_rsin_user_via_api_and_update_klant(
        self, m, mock_captcha2, mock_captcha, mock_send_confirm
    ):
        self.maxDiff = None
        MockAPICreateData.setUpServices()

        # we need to patch the captcha Q&A twice because they are re-generated by the form
        mock_captcha2.return_value = ("", 42)

        klant_config = KlantenSysteemConfig.get_solo()
        klant_config.primary_backend = KlantenServiceType.ESUITE.value
        klant_config.register_contact_via_api = True
        klant_config.send_email_confirmation = True
        klant_config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.register_type = "Melding"
        esuite_config.register_employee_id = "FooVonBar"
        esuite_config.save()

        for (
            use_rsin_for_innNnpId_query_parameter,
            send_klantcontact_confirmation_email,
        ) in [(True, False), (True, False)]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                # NOTE Explicitly creating a new Mocker object here, because for some reason
                # `m` is overridden somewhere, which causes issues when `MockAPIData.setUpOASMocks`
                # is run for the second time
                with requests_mock.Mocker() as m:
                    esuite_config.use_rsin_for_innNnpId_query_parameter = (
                        use_rsin_for_innNnpId_query_parameter
                    )
                    esuite_config.send_klantcontact_confirmation_email = (
                        send_klantcontact_confirmation_email
                    )
                    esuite_config.save()

                    data = MockAPICreateData()
                    data.install_mocks_eherkenning_missing_contact_info(
                        m, use_rsin=use_rsin_for_innNnpId_query_parameter
                    )

                    subject = ContactFormSubjectFactory(
                        subject="Aanvraag document",
                        esuite_subject_code="afdeling-xyz",
                        esuite_config=esuite_config,
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
                            "verzendBevestigingsmail": send_klantcontact_confirmation_email,
                            "rol": KlantContactRol.BELANGHEBBENDE,
                        },
                    )

                    self.assertTimelineLog("retrieved klant for BSN or KVK user")
                    self.assertTimelineLog(
                        "patched klant from user with missing fields: emailadres, telefoonnummer"
                    )
                    self.assertTimelineLog("registered contactmoment via eSuite")

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

        klant_config = KlantenSysteemConfig.get_solo()
        klant_config.primary_backend = KlantenServiceType.ESUITE.value
        klant_config.register_contact_via_api = True
        klant_config.save()

        esuite_config = ESuiteKlantConfig.get_solo()
        esuite_config.register_contact_moment = True
        esuite_config.register_bronorganisatie_rsin = "123456789"
        esuite_config.register_type = "Melding"
        esuite_config.register_employee_id = "FooVonBar"
        esuite_config.save()

        data = MockAPICreateData()
        data.install_mocks_anon(m)

        subject = ContactFormSubjectFactory(
            subject="Aanvraag document",
            esuite_subject_code="afdeling-xyz",
            esuite_config=esuite_config,
        )
        for send in [True, False]:
            with self.subTest(send=send):
                klant_config.send_email_confirmation = send
                klant_config.save()

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
