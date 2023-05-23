from django.contrib import messages
from django.core import mail
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import requests_mock
from django_webtest import WebTest

from open_inwoner.accounts.tests.factories import DigidUserFactory
from open_inwoner.openklant.models import ContactFormSubject, OpenKlantConfig
from open_inwoner.openklant.tests.data import MockAPICreateData
from open_inwoner.openklant.tests.factories import ContactFormSubjectFactory
from open_inwoner.openzaak.tests.factories import ServiceFactory
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin


@requests_mock.Mocker()
class ContactFormTestCase(ClearCachesMixin, DisableRequestLogMixin, WebTest):
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

        self.assertTrue(config.has_form_configuration())

    def test_no_form_shown_if_not_has_configuration(self, m):
        # set nothing
        config = OpenKlantConfig.get_solo()
        self.assertFalse(config.has_form_configuration())

        response = self.app.get(self.url)
        self.assertContains(response, _("Contact formulier niet geconfigureerd."))
        self.assertEqual(0, len(response.pyquery("#contact-form")))

    def test_form_requires_either_email_or_phonenumber(self, m):
        config = OpenKlantConfig.get_solo()
        config.register_email = "example@example.com"
        config.save()
        subject = ContactFormSubjectFactory(config=config)

        response = self.app.get(self.url)
        form = response.forms["contact-form"]
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

    def test_submit_and_register_via_email(self, m):
        config = OpenKlantConfig.get_solo()
        config.register_email = "example@example.com"
        config.save()
        subject = ContactFormSubjectFactory(config=config)

        response = self.app.get(self.url)
        form = response.forms["contact-form"]
        form["subject"].select(text=subject.subject)
        form["first_name"] = "Foo"
        form["infix"] = "de"
        form["last_name"] = "Bar"
        form["email"] = "foo@example.com"
        form["phonenumber"] = "0612345678"
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
        self.assertIn("0612345678", email.body)
        self.assertIn("hey!\n\nwaddup?", email.body)

    def test_submit_and_register_anon_via_api(self, m):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.save()

        data = MockAPICreateData()
        data.install_mocks_anon(m)

        subject = ContactFormSubjectFactory(config=config)

        response = self.app.get(self.url)
        form = response.forms["contact-form"]
        form["subject"].select(text=subject.subject)
        form["first_name"] = "Foo"
        form["infix"] = "de"
        form["last_name"] = "Bar"
        form["email"] = "foo@example.com"
        form["phonenumber"] = "0612345678"
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
                "telefoonnummer": "0612345678",
            },
        )
        contactmoment_create_data = data.matchers[1].request_history[0].json()
        self.assertEqual(
            contactmoment_create_data,
            {
                "bronorganisatie": "123456789",
                "onderwerp": subject.subject,
                "tekst": "hey!\n\nwaddup?",
                "type": "contact-formulier",
            },
        )
        kcm_create_data = data.matchers[2].request_history[0].json()
        self.assertEqual(
            kcm_create_data,
            {
                "contactmoment": "https://contactmomenten.nl/api/v1/contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
                "klant": "https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            },
        )

    def test_submit_and_register_bsn_user_via_api(self, m):
        MockAPICreateData.setUpServices()

        config = OpenKlantConfig.get_solo()
        config.register_contact_moment = True
        config.register_bronorganisatie_rsin = "123456789"
        config.save()

        data = MockAPICreateData()
        data.install_mocks_digid(m)

        subject = ContactFormSubjectFactory(config=config)

        response = self.app.get(self.url, user=data.user)
        form = response.forms["contact-form"]
        form["subject"].select(text=subject.subject)
        form["first_name"] = "Foo"
        form["infix"] = "de"
        form["last_name"] = "Bar"
        form["email"] = "foo@example.com"
        form["phonenumber"] = "0612345678"
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
        self.assertEqual(
            contactmoment_create_data,
            {
                "bronorganisatie": "123456789",
                "onderwerp": subject.subject,
                "tekst": "hey!\n\nwaddup?",
                "type": "contact-formulier",
            },
        )
        kcm_create_data = data.matchers[2].request_history[0].json()
        self.assertEqual(
            kcm_create_data,
            {
                "contactmoment": "https://contactmomenten.nl/api/v1/contactmoment/aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
                "klant": "https://klanten.nl/api/v1/klant/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            },
        )
