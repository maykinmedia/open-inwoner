import uuid
from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import signals
from django.test import modify_settings, override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

import requests_mock
from django_webtest import TransactionWebTest
from freezegun import freeze_time
from pyquery import PyQuery
from zgw_consumers.api_models.base import factory

from open_inwoner.accounts.signals import update_user_on_login
from open_inwoner.accounts.tests.factories import DigidUserFactory, UserFactory
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.tests import cms_tools
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.openklant.api_models import ContactMoment, Klant, KlantContactMoment
from open_inwoner.openklant.constants import KlantenServiceType, Status
from open_inwoner.openklant.models import (
    ContactFormSubject,
    ESuiteKlantConfig,
    KlantContactMomentAnswer,
    KlantenSysteemConfig,
)
from open_inwoner.openklant.services import eSuiteVragenService
from open_inwoner.openklant.tests.data import MockAPIReadData
from open_inwoner.openklant.tests.mocks import MockOpenKlant2Service
from open_inwoner.openzaak.models import OpenZaakConfig, ZGWApiGroupConfig
from open_inwoner.utils.test import ClearCachesMixin, DisableRequestLogMixin
from open_inwoner.utils.url import uuid_from_url

from .factories import KlantContactMomentAnswerFactory


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
        self.user = DigidUserFactory(
            email="test@example.com",
            phonenumber="0100000000",
        )

        super().setUp()
        signals.user_logged_in.disconnect(receiver=update_user_on_login)

        MockAPIReadData.setUpServices()
        self.api_group = ZGWApiGroupConfig.objects.get()

        self.klant_config = ESuiteKlantConfig.get_solo()
        self.klant_config.exclude_contactmoment_kanalen = ["intern_initiatief"]
        self.klant_config.register_bronorganisatie_rsin = "123456789"
        self.klant_config.save()

        # for testing replacement of e-suite "onderwerp" code with OIP configured subject
        self.contactformsubject = ContactFormSubject.objects.create(
            subject="oip_subject",
            esuite_subject_code="e_suite_subject_code",
            esuite_config=self.klant_config,
        )

        self.config = KlantenSysteemConfig.get_solo()
        self.config.primary_backend = KlantenServiceType.ESUITE.value
        self.config.save()

        # Create CMS pages for testing (required for request.current_page to be set)
        cms_tools.create_homepage()
        self.cases_page = cms_tools.create_apphook_page(
            CasesApphook, title="Mijn Aanvragen"
        )

    def test_contactmoment_list_bsn(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)

        # make sure internal contactmoment is present in data (should be excluded from kcms in view)
        assert data.contactmoment_intern

        detail_url_esuite = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.ESUITE.value,
                "kcm_uuid": uuid_from_url(data.klant_contactmoment["url"]),
            },
        )
        detail_url_openklant2 = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.OPENKLANT2.value,
                "kcm_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            },
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["page_obj"].object_list
        cm_data = data.contactmoment

        self.assertEqual(len(kcms), 2)
        self.assertEqual(
            kcms[0],
            {
                "identification": "openklant2_identification",
                "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "api_source_uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"),
                "subject": "openklant2_subject",
                "question_text": "hello?",
                "answer_text": "no",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "status": "Onbekend",
                "channel": "email",
                "new_answer_available": False,
                "api_service": KlantenServiceType.OPENKLANT2,
            },
        )
        self.assertEqual(
            kcms[1],
            {
                "identification": cm_data["identificatie"],
                "api_source_url": cm_data["url"],
                "api_source_uuid": uuid_from_url(cm_data["url"]),
                "subject": self.contactformsubject.subject,
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"],
                "new_answer_available": False,
                "api_service": KlantenServiceType.ESUITE,
            },
        )

        kcm = factory(KlantContactMoment, data.klant_contactmoment)
        kcm.contactmoment = factory(ContactMoment, data.contactmoment)
        kcm.klant = factory(Klant, data.klant_bsn)

        mock_get_kcm_answer_mapping.assert_called_once_with(
            [kcm.contactmoment], data.user
        )

        status_item = response.pyquery.find(
            f".list-item__caption:contains('{_('Status')}')"
        ).parent()

        self.assertIn(f"{_('Status')}\n{_('Onbekend')}", status_item.text())
        self.assertIn(f"{_('Status')}\n{_('Afgehandeld')}", status_item.text())
        self.assertNotIn(_("Nieuw antwoord beschikbaar"), response.text)

    def test_contactmoment_list_pagination(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)
        list_url = reverse("cases:contactmoment_list")

        with patch(
            "open_inwoner.accounts.views.contactmoments.KlantContactMomentListView.paginate_by",
            1,
        ):
            # Test first page (default)
            response = self.app.get(list_url, user=data.user)
            kcms = response.context["page_obj"].object_list

            self.assertEqual(len(kcms), 1)
            self.assertEqual(kcms[0]["identification"], "openklant2_identification")

            # Test second page
            response = self.app.get(list_url, {"page": "2"}, user=data.user)
            kcms = response.context["page_obj"].object_list

            self.assertEqual(len(kcms), 1)
            self.assertEqual(
                kcms[0]["identification"], data.contactmoment["identificatie"]
            )

    @freeze_time("2022-01-01")
    def test_contactmoment_list_bsn_new_answer_available(
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

        detail_url_esuite = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.ESUITE.value,
                "kcm_uuid": uuid_from_url(data.klant_contactmoment["url"]),
            },
        )
        detail_url_openklant2 = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.OPENKLANT2.value,
                "kcm_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            },
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["page_obj"].object_list
        cm_data = data.contactmoment

        self.assertEqual(len(kcms), 2)
        self.assertEqual(
            kcms[0],
            {
                "identification": "openklant2_identification",
                "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "api_source_uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"),
                "subject": "openklant2_subject",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "question_text": "hello?",
                "answer_text": "no",
                "status": "Onbekend",
                "channel": "email",
                "new_answer_available": False,
                "api_service": KlantenServiceType.OPENKLANT2,
            },
        )
        self.assertEqual(
            kcms[1],
            {
                "identification": cm_data["identificatie"],
                "api_source_url": cm_data["url"],
                "api_source_uuid": uuid_from_url(cm_data["url"]),
                "subject": self.contactformsubject.subject,
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "status": str(Status.afgehandeld.label),
                "channel": cm_data["kanaal"],
                "new_answer_available": True,
                "api_service": KlantenServiceType.ESUITE,
            },
        )

        kcm = factory(KlantContactMoment, data.klant_contactmoment)
        kcm.contactmoment = factory(ContactMoment, data.contactmoment)
        kcm.klant = factory(Klant, data.klant_bsn)

        mock_get_kcm_answer_mapping.assert_called_once_with(
            [kcm.contactmoment], data.user
        )

        status_item = response.pyquery.find(
            f".list-item__caption:contains('{_('Status')}')"
        ).parent()

        self.assertIn(f"{_('Status')}\n{_('Onbekend')}", status_item.text())
        self.assertIn(f"{_('Status')}\n{_('Afgehandeld')}", status_item.text())
        self.assertIn(_("Nieuw antwoord beschikbaar"), response.text)

    def test_contactmoment_list_kvk_or_rsin(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        for use_rsin_for_innNnpId_query_parameter in [True]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = ESuiteKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                data = MockAPIReadData().install_mocks(m)

                detail_url_esuite = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "api_service": KlantenServiceType.ESUITE.value,
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment2["url"]),
                    },
                )
                detail_url_openklant2 = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "api_service": KlantenServiceType.OPENKLANT2.value,
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment["url"]),
                    },
                )
                list_url = reverse("cases:contactmoment_list")
                response = self.app.get(list_url, user=data.eherkenning_user)

                kcms = response.context["page_obj"].object_list
                cm_data = data.contactmoment2

                self.assertEqual(len(kcms), 2)
                self.assertEqual(
                    kcms[0],
                    {
                        "identification": "openklant2_identification",
                        "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                        "api_source_uuid": uuid.UUID(
                            "aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"
                        ),
                        "subject": "openklant2_subject",
                        "question_text": "hello?",
                        "answer_text": "no",
                        "registered_date": datetime.fromisoformat(
                            "2024-01-01T12:00:00Z"
                        ),
                        "status": "Onbekend",
                        "channel": "email",
                        "new_answer_available": False,
                        "api_service": KlantenServiceType.OPENKLANT2,
                    },
                )
                self.assertEqual(
                    kcms[1],
                    {
                        "identification": cm_data["identificatie"],
                        "api_source_url": cm_data["url"],
                        "api_source_uuid": uuid_from_url(cm_data["url"]),
                        "subject": self.contactformsubject.subject,
                        "question_text": cm_data["tekst"],
                        "answer_text": cm_data["antwoord"],
                        "registered_date": datetime.fromisoformat(
                            cm_data["registratiedatum"]
                        ),
                        "status": Status.afgehandeld.label.title(),
                        "channel": cm_data["kanaal"],
                        "new_answer_available": False,
                        "api_service": KlantenServiceType.ESUITE,
                    },
                )

    def test_contactmoment_list_vestiging(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user_vestiging)

        for use_rsin_for_innNnpId_query_parameter in [True]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = ESuiteKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                detail_url_esuite = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "api_service": KlantenServiceType.ESUITE.value,
                        "kcm_uuid": uuid_from_url(
                            data.klant_contactmoment_vestiging["url"]
                        ),
                    },
                )
                list_url = reverse("cases:contactmoment_list")

                response = self.client.get(list_url)

                kcms = response.context["page_obj"].object_list
                cm_data = data.contactmoment_vestiging

                self.assertEqual(len(kcms), 2)
                self.assertEqual(
                    kcms[0],
                    {
                        "identification": "openklant2_identification",
                        "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                        "api_source_uuid": uuid.UUID(
                            "aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"
                        ),
                        "subject": "openklant2_subject",
                        "question_text": "hello?",
                        "answer_text": "no",
                        "registered_date": datetime.fromisoformat(
                            "2024-01-01T12:00:00Z"
                        ),
                        "status": "Onbekend",
                        "channel": "email",
                        "new_answer_available": False,
                        "api_service": KlantenServiceType.OPENKLANT2,
                    },
                )
                self.assertEqual(
                    kcms[1],
                    {
                        "identification": cm_data["identificatie"],
                        "api_source_url": cm_data["url"],
                        "api_source_uuid": uuid.UUID(
                            "aaaaaaaa-aaaa-aaaa-aaaa-eeeeeeeeeeee"
                        ),
                        "subject": self.contactformsubject.subject,
                        "question_text": cm_data["tekst"],
                        "answer_text": cm_data["antwoord"],
                        "registered_date": datetime.fromisoformat(
                            cm_data["registratiedatum"]
                        ),
                        "status": Status.afgehandeld.label,
                        "channel": cm_data["kanaal"],
                        "new_answer_available": False,
                        "api_service": KlantenServiceType.ESUITE,
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

    def test_contactmoment_detail_esuite_bsn(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.ESUITE.value,
                "kcm_uuid": uuid_from_url(data.klant_contactmoment["url"]),
            },
        )
        response = self.app.get(detail_url, user=data.user)

        kcm = response.context["question"]
        cm_data = data.contactmoment

        self.assertEqual(response.context["zaak"], None)
        self.assertEqual(
            kcm,
            {
                "identification": cm_data["identificatie"],
                "api_source_url": cm_data["url"],
                "api_source_uuid": uuid_from_url(cm_data["url"]),
                "subject": self.contactformsubject.subject,
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "status": Status.afgehandeld.label,
                "channel": cm_data["kanaal"],
                "new_answer_available": False,
                "api_service": KlantenServiceType.ESUITE,
            },
        )

    def test_contactmoment_detail_openklant2(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.OPENKLANT2.value,
                "kcm_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            },
        )
        response = self.app.get(detail_url, user=self.user)

        kcm = response.context["question"]

        self.assertEqual(
            kcm,
            {
                "identification": "openklant2_identification",
                "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "api_source_uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"),
                "subject": "openklant2_subject",
                "question_text": "hello?",
                "answer_text": "no",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "status": "Onbekend",
                "channel": "email",
                "new_answer_available": False,
                "api_service": KlantenServiceType.OPENKLANT2,
            },
        )

    def test_contactmoment_detail_bsn_with_zaak(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m, link_objectcontactmomenten=True)

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.ESUITE.value,
                "kcm_uuid": uuid_from_url(data.klant_contactmoment["url"]),
            },
        )
        response = self.app.get(detail_url, user=data.user)

        kcm = response.context["question"]
        cm_data = data.contactmoment

        self.assertIsNotNone(response.context["zaak"])
        self.assertEqual(response.context["zaak"].url, data.zaak["url"])
        self.assertEqual(response.context["zaak"].identificatie, "053ESUITE5422021")
        self.assertEqual(
            kcm,
            {
                "identification": cm_data["identificatie"],
                "api_source_url": cm_data["url"],
                "api_source_uuid": uuid_from_url(cm_data["url"]),
                "subject": self.contactformsubject.subject,
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "status": Status.afgehandeld.label,
                "channel": cm_data["kanaal"],
                "new_answer_available": False,
                "api_service": KlantenServiceType.ESUITE,
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

    def test_contactmoment_detail_bsn_with_zaak_reformat_esuite_id(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m, link_objectcontactmomenten=True)

        oz_config = OpenZaakConfig.get_solo()
        oz_config.reformat_esuite_zaak_identificatie = True
        oz_config.save()

        detail_url = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.ESUITE.value,
                "kcm_uuid": uuid_from_url(data.klant_contactmoment["url"]),
            },
        )
        response = self.app.get(detail_url, user=data.user)

        kcm = response.context["question"]
        cm_data = data.contactmoment

        self.assertIsNotNone(response.context["zaak"])
        self.assertEqual(response.context["zaak"].url, data.zaak["url"])
        self.assertEqual(
            kcm,
            {
                "identification": cm_data["identificatie"],
                "api_source_url": cm_data["url"],
                "api_source_uuid": uuid_from_url(cm_data["url"]),
                "subject": self.contactformsubject.subject,
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "status": Status.afgehandeld.label,
                "channel": cm_data["kanaal"],
                "new_answer_available": False,
                "api_service": KlantenServiceType.ESUITE,
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

    def test_contactmoment_list_subject_duplicate_esuite_codes(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        """
        Assert that the first OIP subject is used if several are mapped to the same e-suite code
        """
        data = MockAPIReadData().install_mocks(m)

        ContactFormSubject.objects.create(
            subject="control_subject_for_duplicate_code",
            esuite_subject_code=self.contactformsubject.esuite_subject_code,
            esuite_config=ESuiteKlantConfig.get_solo(),
        )

        detail_url_esuite = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.ESUITE.value,
                "kcm_uuid": uuid_from_url(data.klant_contactmoment["url"]),
            },
        )
        detail_url_openklant2 = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.OPENKLANT2.value,
                "kcm_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            },
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["page_obj"].object_list
        cm_data = data.contactmoment

        self.assertEqual(len(kcms), 2)
        self.assertEqual(
            kcms[0],
            {
                "identification": "openklant2_identification",
                "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "api_source_uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"),
                "subject": "openklant2_subject",
                "question_text": "hello?",
                "answer_text": "no",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "status": "Onbekend",
                "channel": "email",
                "new_answer_available": False,
                "api_service": KlantenServiceType.OPENKLANT2,
            },
        )
        self.assertEqual(
            kcms[1],
            {
                "identification": cm_data["identificatie"],
                "api_source_url": cm_data["url"],
                "api_source_uuid": uuid_from_url(cm_data["url"]),
                "subject": self.contactformsubject.subject,
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "status": Status.afgehandeld.label,
                "channel": cm_data["kanaal"],
                "new_answer_available": False,
                "api_service": KlantenServiceType.ESUITE,
            },
        )

    def test_contactmoment_list_subject_no_mapping_fallback(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        """
        Assert that the e-suite subject code is displayed if no mapping is configured in OIP
        """
        data = MockAPIReadData().install_mocks(m)

        self.contactformsubject.delete()

        detail_url_esuite = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.ESUITE.value,
                "kcm_uuid": uuid_from_url(data.klant_contactmoment["url"]),
            },
        )
        detail_url_openklant2 = reverse(
            "cases:contactmoment_detail",
            kwargs={
                "api_service": KlantenServiceType.OPENKLANT2.value,
                "kcm_uuid": "aaaaaaaa-aaaa-aaaa-aaaa-bbbbbbbbbbbb",
            },
        )
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=data.user)

        kcms = response.context["page_obj"].object_list
        cm_data = data.contactmoment

        self.assertEqual(len(kcms), 2)
        self.assertEqual(
            kcms[0],
            {
                "identification": "openklant2_identification",
                "api_source_url": "http://openklant2.nl/api/v1/vragen/aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc",
                "api_source_uuid": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-cccccccccccc"),
                "subject": "openklant2_subject",
                "question_text": "hello?",
                "answer_text": "no",
                "registered_date": datetime.fromisoformat("2024-01-01T12:00:00Z"),
                "status": "Onbekend",
                "channel": "email",
                "new_answer_available": False,
                "api_service": KlantenServiceType.OPENKLANT2,
            },
        )
        self.assertEqual(
            kcms[1],
            {
                "identification": cm_data["identificatie"],
                "api_source_url": cm_data["url"],
                "api_source_uuid": uuid_from_url(cm_data["url"]),
                "subject": self.contactformsubject.esuite_subject_code,
                "question_text": cm_data["tekst"],
                "answer_text": cm_data["antwoord"],
                "registered_date": datetime.fromisoformat(cm_data["registratiedatum"]),
                "status": Status.afgehandeld.label,
                "channel": cm_data["kanaal"],
                "new_answer_available": False,
                "api_service": KlantenServiceType.ESUITE,
            },
        )

    def test_contactmoment_detail_esuite_for_kvk_or_rsin(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                # Avoid having a `KlantContactMomentAnswer` with the same URL for different users
                KlantContactMomentAnswer.objects.all().delete()

                config = ESuiteKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                eherkenning_kvk = f"0000000{int(use_rsin_for_innNnpId_query_parameter)}"

                data = MockAPIReadData(eherkenning_kvk=eherkenning_kvk).install_mocks(m)

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "api_service": KlantenServiceType.ESUITE.value,
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment2["url"]),
                    },
                )
                response = self.app.get(detail_url, user=data.eherkenning_user)

                kcm = response.context["question"]
                cm_data = data.contactmoment2
                self.assertEqual(
                    kcm,
                    {
                        "identification": cm_data["identificatie"],
                        "api_source_url": cm_data["url"],
                        "api_source_uuid": uuid_from_url(cm_data["url"]),
                        "subject": self.contactformsubject.subject,
                        "question_text": cm_data["tekst"],
                        "answer_text": cm_data["antwoord"],
                        "registered_date": datetime.fromisoformat(
                            cm_data["registratiedatum"]
                        ),
                        "status": Status.afgehandeld.label,
                        "channel": cm_data["kanaal"],
                        "new_answer_available": False,
                        "api_service": KlantenServiceType.ESUITE,
                    },
                )

    def test_contactmoment_detail_esuite_vestiging(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user_vestiging)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = ESuiteKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "api_service": KlantenServiceType.ESUITE.value,
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment4["url"]),
                    },
                )
                response = self.client.get(detail_url)

                kcm = response.context["question"]
                cm_data = data.contactmoment_vestiging
                self.assertEqual(
                    kcm,
                    {
                        "identification": cm_data["identificatie"],
                        "api_source_url": cm_data["url"],
                        "api_source_uuid": uuid_from_url(cm_data["url"]),
                        "subject": self.contactformsubject.subject,
                        "question_text": cm_data["tekst"],
                        "answer_text": cm_data["antwoord"],
                        "registered_date": datetime.fromisoformat(
                            cm_data["registratiedatum"]
                        ),
                        "status": Status.afgehandeld.label,
                        "channel": cm_data["kanaal"],
                        "new_answer_available": False,
                        "api_service": KlantenServiceType.ESUITE,
                    },
                )

    def test_cannot_access_detail_for_hoofdvestiging_as_vestiging(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        data = MockAPIReadData().install_mocks(m)
        self.client.force_login(user=data.eherkenning_user_vestiging)

        for use_rsin_for_innNnpId_query_parameter in [True, False]:
            with self.subTest(
                use_rsin_for_innNnpId_query_parameter=use_rsin_for_innNnpId_query_parameter
            ):
                config = ESuiteKlantConfig.get_solo()
                config.use_rsin_for_innNnpId_query_parameter = (
                    use_rsin_for_innNnpId_query_parameter
                )
                config.save()

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "api_service": KlantenServiceType.ESUITE.value,
                        "kcm_uuid": uuid_from_url(data.klant_contactmoment2["url"]),
                    },
                )
                response = self.client.get(detail_url)

                self.assertEqual(response.status_code, 404)

    def test_contactmoment_list_requires_bsn_or_kvk(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        self.klant_config.register_bronorganisatie_rsin = "123456789"
        self.klant_config.save()

        user = UserFactory()
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url, user=user)
        self.assertRedirects(response, reverse("pages-root"))

    def test_contactmoment_list_requires_login(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        list_url = reverse("cases:contactmoment_list")
        response = self.app.get(list_url)
        self.assertRedirects(response, f"{reverse('login')}?next={list_url}")

    def test_contactmoment_detail_requires_bsn_or_kvk(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        user = UserFactory()

        for service in [KlantenServiceType.ESUITE, KlantenServiceType.OPENKLANT2]:
            with self.subTest(api_service=service):
                url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "api_service": service,
                        "kcm_uuid": uuid4(),
                    },
                )
                response = self.app.get(url, user=user)
                self.assertRedirects(response, reverse("pages-root"))

    def test_contactmoment_detail_requires_login(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        for service in [KlantenServiceType.ESUITE, KlantenServiceType.OPENKLANT2]:
            with self.subTest(api_service=service):
                url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={
                        "api_service": service,
                        "kcm_uuid": uuid4(),
                    },
                )
                response = self.app.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_contactmoment_list_accessible_without_contact_registration(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        """
        The contactmomenten list must return 200 even when contact registration
        is fully disabled. Before the fix, ContactFormView.dispatch() raised
        Http404 in this configuration.
        """
        config = KlantenSysteemConfig.get_solo()
        config.primary_backend = ""
        config.register_contact_email = ""
        config.save()

        self.assertFalse(config.contact_registration_enabled)

        response = self.app.get(reverse("cases:contactmoment_list"), user=self.user)

        self.assertEqual(response.status_code, 200)

    def test_contactmoment_list_contact_form_visibility(
        self, m, mock_openklant2_service, mock_get_kcm_answer_mapping
    ):
        """
        The contact form is shown only when both the site toggle and contact
        registration are enabled.
        """
        siteconfig = SiteConfiguration.get_solo()
        siteconfig.contactmoment_contact_form_enabled = True
        siteconfig.save()

        config = KlantenSysteemConfig.get_solo()
        list_url = reverse("cases:contactmoment_list")

        cases = [
            (
                "no registration",
                {"primary_backend": "", "register_contact_email": ""},
                False,
            ),
            (
                "email registration",
                {"primary_backend": "", "register_contact_email": "test@example.com"},
                True,
            ),
        ]
        for label, config_values, expect_form in cases:
            with self.subTest(label):
                for attr, value in config_values.items():
                    setattr(config, attr, value)
                config.save()

                response = self.app.get(list_url, user=self.user)

                self.assertEqual(
                    response.context["contactmoment_contact_form_enabled"], expect_form
                )
                if expect_form:
                    self.assertContains(response, "question-form")
                else:
                    self.assertNotContains(response, "question-form")
