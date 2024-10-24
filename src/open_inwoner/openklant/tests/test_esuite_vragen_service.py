from datetime import datetime

from django.test import TestCase, override_settings
from django.urls import reverse

import requests_mock

from open_inwoner.accounts.tests.factories import UserFactory
from open_inwoner.openklant.constants import Status
from open_inwoner.openklant.models import ContactFormSubject, OpenKlantConfig
from open_inwoner.openklant.services import eSuiteVragenService
from open_inwoner.openklant.tests.data import MockAPIReadData
from open_inwoner.utils.test import uuid_from_url


@requests_mock.Mocker()
@override_settings(ROOT_URLCONF="open_inwoner.cms.tests.urls")
class eSuiteVragenServiceTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        MockAPIReadData.setUpServices()
        self.service = eSuiteVragenService()
        self.user = UserFactory()
        klanten_config = OpenKlantConfig.get_solo()
        klanten_config.exclude_contactmoment_kanalen = ["intern_initiatief"]
        klanten_config.save()

        self.contactformsubject = ContactFormSubject.objects.create(
            subject="oip_subject",
            subject_code="e_suite_subject_code",
            config=klanten_config,
        )

    def test_list_questions_returns_expected_rows(self, m):
        data = MockAPIReadData().install_mocks(m)
        config = OpenKlantConfig.get_solo()

        for user, params, expected_klantcontact, expected_contactmoment, use_rsin in (
            (
                data.user,
                {"user_bsn": "100000001"},
                data.klant_contactmoment,
                data.contactmoment,
                False,
            ),
            (
                data.eherkenning_user,
                {"user_kvk_or_rsin": "12345678"},
                data.klant_contactmoment2,
                data.contactmoment2,
                False,
            ),
            (
                data.eherkenning_user,
                {"user_kvk_or_rsin": "12345678", "vestigingsnummer": "1234"},
                data.klant_contactmoment4,
                data.contactmoment_vestiging,
                False,
            ),
            (
                data.eherkenning_user,
                # RSIN case
                {"user_kvk_or_rsin": "000000000", "vestigingsnummer": "1234"},
                data.klant_contactmoment4,
                data.contactmoment_vestiging,
                True,
            ),
            (
                data.eherkenning_user,
                # RSIN case
                {"user_kvk_or_rsin": "000000000"},
                data.klant_contactmoment2,
                data.contactmoment2,
                True,
            ),
        ):
            with self.subTest(f"{user=} {params=} {use_rsin=}"):
                config.use_rsin_for_innNnpId_query_parameter = use_rsin
                config.save()
                questions = list(self.service.list_questions(params, user))

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={"kcm_uuid": uuid_from_url(expected_klantcontact["url"])},
                )
                self.assertEqual(len(questions), 1)
                self.assertEqual(
                    questions[0],
                    {
                        "registered_date": datetime.fromisoformat(
                            expected_contactmoment["registratiedatum"]
                        ),
                        "channel": expected_contactmoment["kanaal"].title(),
                        "question_text": expected_contactmoment["tekst"],
                        "subject": self.contactformsubject.subject,
                        "answer_text": expected_contactmoment["antwoord"],
                        "identification": expected_contactmoment["identificatie"],
                        "status": str(Status.afgehandeld.label),
                        "case_detail_url": detail_url,
                        "new_answer_available": False,
                    },
                )
                m.reset_mock()
                data = MockAPIReadData().install_mocks(m)

    def test_retrieve_question_returns_expected_result(self, m):
        data = MockAPIReadData().install_mocks(m)
        config = OpenKlantConfig.get_solo()

        for user, params, expected_klantcontact, expected_contactmoment, use_rsin in (
            (
                data.user,
                {"user_bsn": "100000001"},
                data.klant_contactmoment,
                data.contactmoment,
                False,
            ),
            (
                data.eherkenning_user,
                {"user_kvk_or_rsin": "12345678"},
                data.klant_contactmoment2,
                data.contactmoment2,
                False,
            ),
            (
                data.eherkenning_user,
                {"user_kvk_or_rsin": "12345678", "vestigingsnummer": "1234"},
                data.klant_contactmoment4,
                data.contactmoment_vestiging,
                False,
            ),
            (
                data.eherkenning_user,
                # RSIN case
                {"user_kvk_or_rsin": "000000000", "vestigingsnummer": "1234"},
                data.klant_contactmoment4,
                data.contactmoment_vestiging,
                True,
            ),
            (
                data.eherkenning_user,
                # RSIN case
                {"user_kvk_or_rsin": "000000000"},
                data.klant_contactmoment2,
                data.contactmoment2,
                True,
            ),
        ):
            with self.subTest(f"{user=} {params=} {use_rsin=}"):
                config.use_rsin_for_innNnpId_query_parameter = use_rsin
                config.save()
                question, _ = self.service.retrieve_question(
                    params, expected_klantcontact["uuid"], user
                )

                detail_url = reverse(
                    "cases:contactmoment_detail",
                    kwargs={"kcm_uuid": uuid_from_url(expected_klantcontact["url"])},
                )
                self.assertEqual(
                    question,
                    {
                        "registered_date": datetime.fromisoformat(
                            expected_contactmoment["registratiedatum"]
                        ),
                        "channel": expected_contactmoment["kanaal"].title(),
                        "question_text": expected_contactmoment["tekst"],
                        "subject": self.contactformsubject.subject,
                        "answer_text": expected_contactmoment["antwoord"],
                        "identification": expected_contactmoment["identificatie"],
                        "status": str(Status.afgehandeld.label),
                        "case_detail_url": detail_url,
                        "new_answer_available": False,
                    },
                )
                m.reset_mock()
                data = MockAPIReadData().install_mocks(m)
