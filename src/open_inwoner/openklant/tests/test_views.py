from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from django.test import modify_settings, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import TransactionWebTest
from freezegun import freeze_time
from pyquery import PyQuery
from zgw_consumers.api_models.base import factory

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.api_models import ContactMoment, Klant, KlantContactMoment
from open_inwoner.openklant.constants import KlantenServiceType, Status
from open_inwoner.openklant.models import (
    ContactFormSubject,
    KlantContactMomentAnswer,
    OpenKlantConfig,
)
from open_inwoner.openklant.services import eSuiteVragenService
from open_inwoner.openklant.tests.data import MockAPIReadData
from open_inwoner.openzaak.models import OpenZaakConfig, ZGWApiGroupConfig
from open_inwoner.utils.test import (
    ClearCachesMixin,
    DisableRequestLogMixin,
    set_kvk_branch_number_in_session,
    uuid_from_url,
)

from .factories import KlantContactMomentAnswerFactory


class MockOpenKlant2Service:
    def list_questions(self, fetch_params={}, user=None):
        return [
            {
                "identification": "openklant2_identification",
                "source_url": "http://www.openklant2/test/url",
                "subject": "openklan2_subject",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "case_detail_url": "",
                "api_service": KlantenServiceType.OPENKLANT2,
                "new_answer_available": False,
            }
        ]

    def retrieve_question(self, fetch_params={}, question_uuid="", user=None):
        return (
            {
                "identification": "openklant2_identification",
                "source_url": "http://www.openklant2/test/url",
                "subject": "openklan2_subject",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "case_detail_url": "",
                "api_service": KlantenServiceType.OPENKLANT2,
                "new_answer_available": False,
            },
            None,
        )

    def get_fetch_parameters(self, request=None, user=None, use_vestigingsnummer=False):
        return {"user_bsn": "123456789"}


@requests_mock.Mocker()
@patch.object(eSuiteVragenService, "get_kcm_answer_mapping", autospec=True)
@patch(
    "open_inwoner.accounts.views.contactmoments.OpenKlant2Service",
    return_value=MockOpenKlant2Service(),
)
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
@modify_settings(
    MIDDLEWARE={"remove": ["open_inwoner.kvk.middleware.KvKLoginMiddleware"]}
)
class ContactMomentViewsTestCase(
    ClearCachesMixin, DisableRequestLogMixin, TransactionWebTest
):
    maxDiff = None

    def setUp(self):
        super().setUp()
        MockAPIReadData.setUpServices()
        self.api_group = ZGWApiGroupConfig.objects.get()

        klanten_config = OpenKlantConfig.get_solo()
        klanten_config.exclude_contactmoment_kanalen = ["intern_initiatief"]
        klanten_config.save()

        # for testing replacement of e-suite "onderwerp" code with OIP configured subject
        self.contactformsubject = ContactFormSubject.objects.create(
            subject="oip_subject",
            subject_code="e_suite_subject_code",
            config=klanten_config,
        )

    def test_list_for_bsn(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)

        # make sure internal contactmoment is present in data (should be excluded from kcms in view)
        assert data.contactmoment_intern

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={"kcm_uuid": uuid_from_url(data.klant_contactmoment["url"])},
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["contactmomenten"]
        cm_data = data.contactmoment

        self.assertEqual(len(kcms), 2)
        self.assertEqual(
            kcms[0],
            {
                "identification": "openklant2_identification",
                "source_url": "http://www.openklant2/test/url",
                "subject": "openklan2_subject",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "case_detail_url": "",
                "api_service": KlantenServiceType.OPENKLANT2,
                "new_answer_available": False,
            },
        )
        self.assertEqual(
            kcms[1],
            {
                "identification": cm_data["identificatie"],
                "source_url": cm_data["url"],
                "subject": self.contactformsubject.subject,
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"].title(),
                "case_detail_url": detail_url,
                "api_service": KlantenServiceType.ESUITE,
                "new_answer_available": False,
            },
        )

        kcm = factory(KlantContactMoment, data.klant_contactmoment)
        kcm.contactmoment = factory(ContactMoment, data.contactmoment)
        kcm.klant = factory(Klant, data.klant_bsn)

        mock_get_kcm_answer_mapping.assert_called_once_with(
            [kcm.contactmoment], data.user
        )

        status_item = response.pyquery.find(f"p:contains('{_('Status')}')").parent()

        self.assertIn(f"{_('Status')}\n{_('Onbekend')}", status_item.text())
        self.assertIn(f"{_('Status')}\n{_('Afgehandeld')}", status_item.text())
        self.assertNotIn(_("Nieuw antwoord beschikbaar"), response.text)

    @freeze_time("2022-01-01")
    def test_list_for_bsn_new_answer_available(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)

        # make sure internal contactmoment is present in data (should be excluded from kcms in view)
        assert data.contactmoment_intern

        mock_get_kcm_answer_mapping.return_value = {
            data.klant_contactmoment["url"]: KlantContactMomentAnswerFactory.create(
                user=data.user,
                contactmoment_url=uuid_from_url(
                    data.klant_contactmoment["contactmoment"]
                ),
                is_seen=False,
            )
        }

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={"kcm_uuid": uuid_from_url(data.klant_contactmoment["url"])},
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["contactmomenten"]
        cm_data = data.contactmoment

        self.assertEqual(len(kcms), 2)
        self.assertEqual(
            kcms[0],
            {
                "identification": "openklant2_identification",
                "source_url": "http://www.openklant2/test/url",
                "subject": "openklan2_subject",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "case_detail_url": "",
                "api_service": KlantenServiceType.OPENKLANT2,
                "new_answer_available": False,
            },
        )
        self.assertEqual(
            kcms[1],
            {
                "identification": cm_data["identificatie"],
                "source_url": cm_data["url"],
                "subject": self.contactformsubject.subject,
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"].title(),
                "case_detail_url": detail_url,
                "api_service": KlantenServiceType.ESUITE,
                "new_answer_available": True,
            },
        )

        kcm = factory(KlantContactMoment, data.klant_contactmoment)
        kcm.contactmoment = factory(ContactMoment, data.contactmoment)
        kcm.klant = factory(Klant, data.klant_bsn)

        mock_get_kcm_answer_mapping.assert_called_once_with(
            [kcm.contactmoment], data.user
        )

        status_item = response.pyquery.find(f"p:contains('{_('Status')}')").parent()

        self.assertIn(f"{_('Status')}\n{_('Onbekend')}", status_item.text())
        self.assertIn(f"{_('Status')}\n{_('Afgehandeld')}", status_item.text())
        self.assertIn(_("Nieuw antwoord beschikbaar"), response.text)

    def test_list_for_kvk_or_rsin(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                data = MockAPIReadData().install_mocks(m)

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment2["url"])
                    },
                )
                list_url = reverse("cases:contactmoment_list")
                response = self.app.get(list_url, user=data.eherkenning_user)

                kcms = response.context["contactmomenten"]
                cm_data = data.contactmoment2

                self.assertEqual(len(kcms), 2)
                self.assertEqual(
                    kcms[0],
                    {
                        "identification": "openklant2_identification",
                        "source_url": "http://www.openklant2/test/url",
                        "subject": "openklan2_subject",
                        "registered_date": datetime.fromisoformat(
                            "2024-01-01T12:00:00Z"
                        ),
                        "question_text": "hello?",
                        "answer_text": "no",
                        "status": "Onbekend",
                        "channel": "email",
                        "case_detail_url": "",
                        "api_service": KlantenServiceType.OPENKLANT2,
                        "new_answer_available": False,
                    },
                )
                self.assertEqual(
                    kcms[1],
                    {
                        "identification": cm_data["identificatie"],
                        "source_url": cm_data["url"],
                        "subject": self.contactformsubject.subject,
                        "registered_date": datetime.fromisoformat(
                            cm_data["registratiedatum"]
                        ),
                        "question_text": cm_data["tekst"],
                        "answer_text": cm_data["antwoord"],
                        "status": str(Status.afgehandeld.label),
                        "channel": cm_data["kanaal"].title(),
                        "case_detail_url": detail_url,
                        "api_service": KlantenServiceType.ESUITE,
                        "new_answer_available": False,
                    },
                )

    @set_kvk_branch_number_in_session("1234")
    def test_list_for_vestiging(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment4["url"])
                    },
                )
                list_url = reverse("cases:contactmoment_list")

                response = self.client.get(list_url)

                kcms = response.context["contactmomenten"]
                cm_data = data.contactmoment_vestiging

                self.assertEqual(len(kcms), 2)
                self.assertEqual(
                    kcms[0],
                    {
                        "identification": "openklant2_identification",
                        "source_url": "http://www.openklant2/test/url",
                        "subject": "openklan2_subject",
                        "registered_date": datetime.fromisoformat(
                            "2024-01-01T12:00:00Z"
                        ),
                        "question_text": "hello?",
                        "answer_text": "no",
                        "status": "Onbekend",
                        "channel": "email",
                        "case_detail_url": "",
                        "api_service": KlantenServiceType.OPENKLANT2,
                        "new_answer_available": False,
                    },
                )
                self.assertEqual(
                    kcms[1],
                    {
                        "identification": cm_data["identificatie"],
                        "source_url": cm_data["url"],
                        "subject": self.contactformsubject.subject,
                        "registered_date": datetime.fromisoformat(
                            cm_data["registratiedatum"]
                        ),
                        "question_text": cm_data["tekst"],
                        "answer_text": cm_data["antwoord"],
                        "status": str(Status.afgehandeld.label),
                        "channel": cm_data["kanaal"].title(),
                        "case_detail_url": detail_url,
                        "api_service": KlantenServiceType.ESUITE,
                        "new_answer_available": False,
                    },
                )

    def test_disable_contactmoment_form(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)
        list_url = reverse("cases:contactmoment_list")

        config = SiteConfiguration.get_solo()
        config.contactmoment_contact_form_enabled = False
        config.save()

        response = self.app.get(list_url, user=data.user)

        doc = PyQuery(response.content)

        contactform_scrolldown = doc.find(
            "[data-testid='contactmomenten__contact_form_scrolldown']"
        )
        self.assertEqual(contactform_scrolldown, [])

        contactform = doc.find("[data-testid='contactmomenten__contact_form']")
        self.assertEqual(contactform, [])

    def test_show_detail_for_bsn(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={"kcm_uuid": uuid_from_url(data.klant_contactmoment["url"])},
        )
        response = self.app.get(detail_url, user=data.user)

        kcm = response.context["contactmoment"]
        cm_data = data.contactmoment

        self.assertEqual(response.context["zaak"], None)
        self.assertEqual(
            kcm,
            {
                "identification": cm_data["identificatie"],
                "source_url": cm_data["url"],
                "subject": self.contactformsubject.subject,
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"].title(),
                "case_detail_url": detail_url,
                "api_service": KlantenServiceType.ESUITE,
                "new_answer_available": False,
            },
        )

    def test_show_detail_for_bsn_with_zaak(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m, link_objectcontactmomenten=True)

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={"kcm_uuid": uuid_from_url(data.klant_contactmoment["url"])},
        )
        response = self.app.get(detail_url, user=data.user)

        kcm = response.context["contactmoment"]
        cm_data = data.contactmoment

        self.assertIsNotNone(response.context["zaak"])
        self.assertEqual(response.context["zaak"].url, data.zaak["url"])
        self.assertEqual(response.context["zaak"].identificatie, "053ESUITE5422021")
        self.assertEqual(
            kcm,
            {
                "identification": cm_data["identificatie"],
                "source_url": cm_data["url"],
                "subject": self.contactformsubject.subject,
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"].title(),
                "case_detail_url": detail_url,
                "api_service": KlantenServiceType.ESUITE,
                "new_answer_available": False,
            },
        )

        zaak_link = response.pyquery("#origin_link")

        self.assertIn(_("Terug naar aanvraag"), zaak_link.text())
        self.assertEqual(
            zaak_link.attr("href"),
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": "410bb717-ff3d-4fd8-8357-801e5daf9775",
                    "api_group_id": self.api_group.id,
                },
            ),
        )

        contactmoment_link = response.pyquery("#destination_link")
        self.assertIn(_("Bekijk alle vragen"), contactmoment_link.text())
        self.assertEqual(
            contactmoment_link.attr("href"),
            reverse("cases:contactmoment_list"),
        )

        kcm_local = KlantContactMomentAnswer.objects.get(
            contactmoment_url=data.klant_contactmoment["contactmoment"]
        )

        self.assertEqual(kcm_local.user, data.user)
        self.assertEqual(kcm_local.is_seen, True)

    def test_show_detail_for_bsn_with_zaak_reformat_esuite_id(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m, link_objectcontactmomenten=True)

        oz_config = OpenZaakConfig.get_solo()
        oz_config.reformat_esuite_zaak_identificatie = True
        oz_config.save()

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={"kcm_uuid": uuid_from_url(data.klant_contactmoment["url"])},
        )
        response = self.app.get(detail_url, user=data.user)

        kcm = response.context["contactmoment"]
        cm_data = data.contactmoment

        self.assertIsNotNone(response.context["zaak"])
        self.assertEqual(response.context["zaak"].url, data.zaak["url"])
        self.assertEqual(
            kcm,
            {
                "identification": cm_data["identificatie"],
                "source_url": cm_data["url"],
                "subject": self.contactformsubject.subject,
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"].title(),
                "case_detail_url": detail_url,
                "api_service": KlantenServiceType.ESUITE,
                "new_answer_available": False,
            },
        )

        zaak_link = response.pyquery("#origin_link")
        self.assertIn(_("Terug naar aanvraag"), zaak_link.text())
        self.assertEqual(
            zaak_link.attr("href"),
            reverse(
                "cases:case_detail",
                kwargs={
                    "object_id": "410bb717-ff3d-4fd8-8357-801e5daf9775",
                    "api_group_id": self.api_group.id,
                },
            ),
        )

        contactmoment_link = response.pyquery("#destination_link")
        self.assertIn(_("Bekijk alle vragen"), contactmoment_link.text())
        self.assertEqual(
            contactmoment_link.attr("href"),
            reverse("cases:contactmoment_list"),
        )

    def test_display_contactmoment_subject_duplicate_esuite_codes(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        """
        Assert that the first OIP subject is used if several are mapped to the same e-suite code
        """
        data = MockAPIReadData().install_mocks(m)

        ContactFormSubject.objects.create(
            subject="control_subject_for_duplicate_code",
            subject_code=self.contactformsubject.subject_code,
            config=OpenKlantConfig.get_solo(),
        )

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={"kcm_uuid": uuid_from_url(data.klant_contactmoment["url"])},
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["contactmomenten"]
        cm_data = data.contactmoment

        self.assertEqual(len(kcms), 2)
        self.assertEqual(
            kcms[0],
            {
                "identification": "openklant2_identification",
                "source_url": "http://www.openklant2/test/url",
                "subject": "openklan2_subject",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "case_detail_url": "",
                "api_service": KlantenServiceType.OPENKLANT2,
                "new_answer_available": False,
            },
        )
        self.assertEqual(
            kcms[1],
            {
                "identification": cm_data["identificatie"],
                "source_url": cm_data["url"],
                "subject": self.contactformsubject.subject,
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"].title(),
                "case_detail_url": detail_url,
                "api_service": KlantenServiceType.ESUITE,
                "new_answer_available": False,
            },
        )

    def test_display_contactmoment_subject_no_mapping_fallback(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        """
        Assert that the e-suite subject code is displayed if no mapping is configured in OIP
        """
        data = MockAPIReadData().install_mocks(m)

        self.contactformsubject.delete()

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={"kcm_uuid": uuid_from_url(data.klant_contactmoment["url"])},
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["contactmomenten"]
        cm_data = data.contactmoment

        self.assertEqual(len(kcms), 2)
        self.assertEqual(
            kcms[0],
            {
                "identification": "openklant2_identification",
                "source_url": "http://www.openklant2/test/url",
                "subject": "openklan2_subject",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "case_detail_url": "",
                "api_service": KlantenServiceType.OPENKLANT2,
                "new_answer_available": False,
            },
        )
        self.assertEqual(
            kcms[1],
            {
                "identification": cm_data["identificatie"],
                "source_url": cm_data["url"],
                "subject": self.contactformsubject.subject_code,
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"].title(),
                "case_detail_url": detail_url,
                "api_service": KlantenServiceType.ESUITE,
                "new_answer_available": False,
            },
        )

    def test_show_detail_for_kvk_or_rsin(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                # Avoid having a `KlantContactMomentAnswer` with the same URL for different users
                KlantContactMomentAnswer.objects.all().delete()

                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                data = MockAPIReadData().install_mocks(m)

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment2["url"])
                    },
                )
                response = self.app.get(detail_url, user=data.eherkenning_user)

                kcm = response.context["contactmoment"]
                cm_data = data.contactmoment2
                registratiedatum = datetime.fromisoformat(cm_data["registratiedatum"])
                self.assertEqual(
                    kcm,
                    {
                        "identification": cm_data["identificatie"],
                        "source_url": cm_data["url"],
                        "subject": self.contactformsubject.subject,
                        "registered_date": datetime.fromisoformat(
                            cm_data["registratiedatum"]
                        ),
                        "question_text": cm_data["tekst"],
                        "answer_text": cm_data["antwoord"],
                        "status": str(Status.afgehandeld.label),
                        "channel": cm_data["kanaal"].title(),
                        "case_detail_url": detail_url,
                        "api_service": KlantenServiceType.ESUITE,
                        "new_answer_available": False,
                    },
                )

    @set_kvk_branch_number_in_session("1234")
    def test_show_detail_for_vestiging(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                kcm_uuid = uuid_from_url(data.klant_contactmoment4["url"])
                detail_url = reverse(
                    "cases:contactmoment_detail", kwargs={"kcm_uuid": kcm_uuid}
                )
                response = self.client.get(detail_url)

                kcm = response.context["contactmoment"]
                cm_data = data.contactmoment_vestiging
                registratie_datum = datetime.fromisoformat(cm_data["registratiedatum"])
                self.assertEqual(
                    kcm,
                    {
                        "identification": cm_data["identificatie"],
                        "source_url": cm_data["url"],
                        "subject": self.contactformsubject.subject,
                        "registered_date": datetime.fromisoformat(
                            cm_data["registratiedatum"]
                        ),
                        "question_text": cm_data["tekst"],
                        "answer_text": cm_data["antwoord"],
                        "status": str(Status.afgehandeld.label),
                        "channel": cm_data["kanaal"].title(),
                        "case_detail_url": detail_url,
                        "api_service": KlantenServiceType.ESUITE,
                        "new_answer_available": False,
                    },
                )

    @set_kvk_branch_number_in_session("1234")
    def test_cannot_access_detail_for_hoofdvestiging_as_vestiging(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = OpenKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment2["url"])
                    },
                )
                response = self.client.get(detail_url)

                self.assertEqual(response.status_code, 404)

    def test_list_requires_bsn_or_kvk(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        user = UserFactory()
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=user)
        self.assertRedirects(response, reverse("pages-root"))

    def test_list_requires_login(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url)
        self.assertRedirects(response, f"{reverse('login')}?next={list_url}")

    def test_detail_requires_bsn_or_kvk(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        user = UserFactory()
        url = reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": uuid4()})
        response = self.app.get(url, user=user)
        self.assertRedirects(response, reverse("pages-root"))

    def test_detail_requires_login(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        url = reverse("cases:contactmoment_detail", kwargs={"kcm_uuid": uuid4()})
        response = self.app.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")
