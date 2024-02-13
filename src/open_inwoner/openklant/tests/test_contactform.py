import inspect

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
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin
from open_inwoner.utils.tests.helpers import AssertFormMixin, AssertTimelineLogMixin


@requests_mock.Mocker()
@modify_settings(
    MIDDLEWARE={"remove": ["open_inwoner.kvk.middleware.KvKLoginMiddleware"]}
)
class ContactFormTestCase(
    ClearCachesMixin,
    AssertTimelineLogMixin,
    AssertFormMixin,
    DisableRequestLogMixin,
    WebTest,
):
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
        config.save()

    def test_singleton_has_configuration_method(self, m):
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

    def test_no_form_shown_if_not_has_configuration(self, m):
        # set nothing
        config = OpenKlantConfig.get_solo()
        self.assertFalse(config.has_form_configuration())

        response = self.app.get(self.url)
        self.assertContains(response, _("Contact formulier niet geconfigureerd."))
        self.assertEqual(0, len(response.pyquery("#contactmoment-form")))

    def test_anon_form_requires_either_email_or_phonenumber(self, m):
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
            ),
        )
        form["subject"].select(text=subject.subject)
        form["first_name"] = "Foo"
        form["last_name"] = "Bar"
        form["email"] = ""
        form["phonenumber"] = ""
        form["question"] = "hey!\n\nwaddup?"

        response = form.submit(status=200)
        self.assertEqual(
            response.context["errors"], [_("Vul een e-mailadres of telefoonnummer in.")]
        )

    def test_regular_auth_form_fills_email_and_phonenumber(self, m):
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

    def test_expected_ordered_subjects_are_shown(self, m):
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

    def test_submit_and_register_via_email(self, m):
        config = OpenKlantConfig.get_solo()
        config.register_email = "example@example.com"
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

    def test_submit_and_register_anon_via_api_with_klant(self, m):
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
                "tekst": "Onderwerp: Aanvraag document\n\nhey!\n\nwaddup?",
                "type": "Melding",
                "kanaal": "Internet",
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
        self.assertTimelineLog("created klant for anonymous user")
        self.assertTimelineLog("registered contactmoment by API")

    def test_submit_and_register_anon_via_api_without_klant(self, m):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.register_type = "Melding"
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
        Onderwerp: Aanvraag document

        hey!

        waddup?

        Naam: Foo de Bar
        Email: foo@example.com
        Telefoonnummer: +31612345678
        """
        )

        self.assertEqual(
            contactmoment_create_data,
            {
                "medewerkerIdentificatie": {"identificatie": "FooVonBar"},
                "bronorganisatie": "123456789",
                "tekst": text,
                "type": "Melding",
                "kanaal": "Internet",
                "onderwerp": "afdeling-xyz",
            },
        )
        self.assertTimelineLog(
            "could not retrieve or create klant for user, appended info to message"
        )
        self.assertTimelineLog("registered contactmoment by API")

    def test_submit_and_register_bsn_user_via_api(self, m):
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
                "tekst": "Onderwerp: Aanvraag document\n\nhey!\n\nwaddup?",
                "type": "Melding",
                "kanaal": "Internet",
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

    def test_submit_and_register_kvk_or_rsin_user_via_api(self, _m):
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
                            "tekst": "Onderwerp: Aanvraag document\n\nhey!\n\nwaddup?",
                            "type": "Melding",
                            "kanaal": "Internet",
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

    def test_submit_and_register_bsn_user_via_api_and_update_klant(self, m):
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
                "tekst": "Onderwerp: Aanvraag document\n\nhey!\n\nwaddup?",
                "type": "Melding",
                "kanaal": "Internet",
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

    def test_submit_and_register_kvk_or_rsin_user_via_api_and_update_klant(self, _m):
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
                            "tekst": "Onderwerp: Aanvraag document\n\nhey!\n\nwaddup?",
                            "type": "Melding",
                            "kanaal": "Internet",
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
